import asyncio
import base64
import os
import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, RedirectResponse
from paramiko import PKey, SSHClient
from thymis_controller import crud, dependencies, models, modules, utils
from thymis_controller.config import global_settings
from thymis_controller.db_models.deployment_info import DeploymentInfo
from thymis_controller.dependencies import (
    ProjectAD,
    SessionAD,
    TaskControllerAD,
    require_valid_user_session,
)
from thymis_controller.models import device
from thymis_controller.models.state import State
from thymis_controller.routers import task
from thymis_controller.tcp_to_ws import (
    channel_to_websocket,
    tcp_to_websocket,
    websocket_to_channel,
    websocket_to_tcp,
)

router = APIRouter(
    dependencies=[Depends(require_valid_user_session)],
)


@router.get("/state")
def get_state(state: State = Depends(dependencies.get_state)):
    return state


@router.get("/available_modules")
def get_available_modules(request: Request) -> list[models.Module]:
    locale = request.cookies.get("locale", "en")
    return [module.get_model(locale) for module in modules.ALL_MODULES]


@router.patch("/state")
async def update_state(new_state: Request, project: ProjectAD):
    new_state = await new_state.json()
    new_state = State.model_validate(new_state)
    return project.write_state_and_reload(new_state)


@router.post("/action/build")
async def build_repo(
    project: ProjectAD,
    task_controller: TaskControllerAD,
    db_session: SessionAD,
):
    task_controller.submit(
        models.BuildProjectTaskSubmission(project_path=str(project.path)),
        db_session=db_session,
    )

    return {"message": "command started"}


router.include_router(task.router)


@router.post("/action/deploy")
async def deploy(
    summary: str,
    session: SessionAD,
    project: ProjectAD,
    task_controller: TaskControllerAD,
):
    project.commit(summary)

    devices: list[models.DeployDeviceInformation] = []

    for device in crud.deployment_info.get_all(session):
        hostkey = models.Hostkey.from_deployment_info(device)
        devices.append(
            models.DeployDeviceInformation(
                identifier=hostkey.identifier,
                host=hostkey.device_host,
                port=22,
                username="root",
            )
        )

    project.update_known_hosts(session)

    task_controller.submit(
        models.DeployDevicesTaskSubmission(
            devices=devices,
            project_path=str(project.path),
            ssh_key_path=str(global_settings.PROJECT_PATH / "id_thymis"),
            known_hosts_path=str(project.known_hosts_path),
        ),
        db_session=session,
    )

    return {"message": "nix deploy started"}


@router.post("/action/build-download-image")
async def build_download_image(
    identifier: str,
    db_session: SessionAD,
    task_controller: TaskControllerAD,
    project: ProjectAD,
):
    project.commit(f"Build image for {identifier}")

    device = next(
        device
        for device in project.read_state().devices
        if device.identifier == identifier
    )

    task_controller.submit(
        models.BuildDeviceImageTaskSubmission(
            project_path=str(project.path),
            device_identifier=identifier,
            device_state=device.model_dump(mode="json"),
            commit=project.repo.head.object.hexsha,
        ),
        db_session=db_session,
    )


@router.post("/action/restart-device")
async def restart_device(
    identifier: str,
    db_session: SessionAD,
    task_controller: TaskControllerAD,
    project: ProjectAD,
):
    for target_host in crud.deployment_info.get_by_config_id(db_session, identifier):
        task_controller.submit(
            models.SSHCommandTaskSubmission(
                target_host=target_host.reachable_deployed_host,
                target_user="root",
                target_port=22,
                command="reboot",
                ssh_key_path=str(global_settings.PROJECT_PATH / "id_thymis"),
                ssh_known_hosts_path=str(project.known_hosts_path),
            ),
            db_session=db_session,
        )


@router.get("/download-image")
async def download_image(
    identifier: str,
    state: State = Depends(dependencies.get_state),
):
    # downloads /tmp/thymis-devices.{identifier} file from filesystem
    # compare identifier with project first
    device = next(device for device in state.devices if device.identifier == identifier)

    if device is None:
        return RedirectResponse("/")

    file_endings = ["img", "qcow2", "iso"]

    # search for file in /tmp/thymis-devices.{identifier}/*
    for root, dirs, files in os.walk(f"/tmp/thymis-devices.{device.identifier}"):
        for file in files:
            if file.endswith(tuple(file_endings)):
                file_path = os.path.join(root, file)
                return FileResponse(
                    file_path,
                    headers={"content-encoding": "none"},
                    filename=f"thymis-image-{device.identifier}.img",
                )

    raise HTTPException(status_code=404, detail="Image not found")


@router.websocket("/notification")
async def notification_websocket(websocket: WebSocket):
    await websocket.state.notification_manager.connect(websocket)


@router.get("/history", tags=["history"])
def get_history(project: ProjectAD):
    return project.get_history()


@router.post("/history/revert-commit", tags=["history"])
def revert_commit(
    commit_sha: str,
    project: ProjectAD,
):
    project.revert_commit(commit_sha)
    return {"message": "reverted commit"}


@router.get("/history/remotes", tags=["history"])
def get_remotes(project: ProjectAD):
    return project.get_remotes()


@router.post("/action/update")
async def update(
    project: ProjectAD,
    task_controller: TaskControllerAD,
    db_session: SessionAD,
):
    project.reload_from_disk()
    project.create_update_task(task_controller, db_session)

    return {"message": "update started"}


@router.websocket("/vnc/{deployment_info_id}")
async def vnc_websocket(
    deployment_info_id: uuid.UUID,
    db_session: SessionAD,
    websocket: WebSocket,
    state: State = Depends(dependencies.get_state),
):
    deployment_info = crud.deployment_info.get_by_id(db_session, deployment_info_id)

    if device is None or deployment_info.reachable_deployed_host is None:
        await websocket.close()
        return

    await websocket.accept()

    tcp_ip = deployment_info.reachable_deployed_host
    tcp_port = 5900
    try:
        tcp_reader, tcp_writer = await asyncio.open_connection(tcp_ip, tcp_port)
    except Exception as e:
        await websocket.send_text(str(e))
        await websocket.close()
        return

    tcp_to_ws_task = asyncio.create_task(tcp_to_websocket(tcp_reader, websocket))
    ws_to_tcp_task = asyncio.create_task(websocket_to_tcp(tcp_writer, websocket))

    try:
        await asyncio.gather(tcp_to_ws_task, ws_to_tcp_task)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        tcp_to_ws_task.cancel()
        ws_to_tcp_task.cancel()


@router.get(
    "/deployment_infos_by_config_id/{deployed_config_id}",
    response_model=list[device.DeploymentInfo],
)
def get_deployment_infos_by_config_id(db_session: SessionAD, deployed_config_id: str):
    """
    Gets the deployment infos for all devices with the given deployed_config_id
    """
    return map(
        lambda x: x.to_dict(),
        crud.deployment_info.get_by_config_id(db_session, deployed_config_id),
    )


@router.get("/deployment_info/{id}", response_model=models.DeploymentInfo)
def get_deployment_info(db_session: SessionAD, id: uuid.UUID):
    """
    Get a specific deployment_info by id
    """
    deployment_info = crud.deployment_info.get_by_id(db_session, id)
    if not deployment_info:
        raise HTTPException(status_code=404, detail="Deployment info not found")
    return deployment_info


@router.get("/deployment_info", response_model=list[models.DeploymentInfo])
def get_all_deployment_infos(db_session: SessionAD):
    """
    Get all deployment_infos
    """
    return map(lambda x: x.to_dict(), crud.deployment_info.get_all(db_session))


@router.patch("/deployment_info/{id}", response_model=models.DeploymentInfo)
def update_deployment_info(
    db_session: SessionAD,
    id: uuid.UUID,
    deployment_info: models.CreateDeploymentInfoLegacyHostkeyRequest,
    project: ProjectAD,
):
    """
    Update a deployment_info
    """
    deployment_info = crud.deployment_info.update(
        db_session,
        id,
        ssh_public_key=deployment_info.ssh_public_key,
        deployed_config_id=deployment_info.deployed_config_id,
        reachable_deployed_host=deployment_info.reachable_deployed_host,
    )
    if not deployment_info:
        raise HTTPException(status_code=404, detail="Deployment info not found")
    project.update_known_hosts(db_session)
    return deployment_info


@router.post("/create_deployment_info", response_model=models.DeploymentInfo)
def create_deployment_info(
    db_session: SessionAD,
    deployment_info: models.CreateDeploymentInfoLegacyHostkeyRequest,
    project: ProjectAD,
):
    """
    Create a deployment_info
    """
    result = crud.deployment_info.create(
        db_session,
        ssh_public_key=deployment_info.ssh_public_key,
        deployed_config_id=deployment_info.deployed_config_id,
        reachable_deployed_host=deployment_info.reachable_deployed_host,
    ).to_dict()
    project.update_known_hosts(db_session)
    return result


@router.post("/rename_config_id_legacy")
def rename_config_id_legacy(
    db_session: SessionAD,
    old_config_id: str,
    new_config_id: str,
    project: ProjectAD,
):
    """
    Rename a config_id in the database
    """
    crud.deployment_info.rename_config_id_for_deployment_without_commit(
        db_session, old_config_id, new_config_id
    )
    project.update_known_hosts(db_session)
    return {"message": "config_id renamed"}


HOST_PATTERN = r"^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$"


@router.post("/scan-public-key", response_model=str)
# regex host
def scan_public_key(
    host: Annotated[
        str,
        Query(
            pattern=HOST_PATTERN,
        ),
    ]
):
    """
    Scan a public key for a device
    """
    host = re.match(HOST_PATTERN, host).group(0)
    assert host is not None
    # TODO maybe return rsa key if no ed25519 key is found
    for address, key in utils.ssh_keyscan_host(host):
        if key.startswith("ssh-ed25519"):
            return key
    else:
        raise HTTPException(status_code=400, detail="No valid public key found")


@router.websocket("/terminal/{deployment_info_id}")
async def terminal_websocket(
    deployment_info_id: uuid.UUID,
    db_session: SessionAD,
    websocket: WebSocket,
    project: ProjectAD,
):
    deployment_info = crud.deployment_info.get_by_id(db_session, deployment_info_id)

    if deployment_info is None or deployment_info.reachable_deployed_host is None:
        await websocket.close()
        return

    await websocket.accept()

    tcp_ip = deployment_info.reachable_deployed_host
    tcp_port = 22

    client = SSHClient()
    keytype, key = deployment_info.ssh_public_key.split(" ", 1)
    client.get_host_keys().add(
        deployment_info.reachable_deployed_host,
        keytype,
        PKey.from_type_string(keytype, base64.b64decode(key)),
    )

    pkey: PKey = PKey.from_path(global_settings.PROJECT_PATH / "id_thymis")

    try:
        channel = await run_in_threadpool(
            connect_to_ssh_shell, client, tcp_ip, tcp_port, pkey
        )
    except Exception as e:
        await websocket.send_bytes(str(e).encode())
        await websocket.close()
        client.close()
        return

    channel_to_ws_task = asyncio.create_task(channel_to_websocket(channel, websocket))
    ws_to_channel_task = asyncio.create_task(websocket_to_channel(channel, websocket))

    try:
        await asyncio.gather(channel_to_ws_task, ws_to_channel_task)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        channel_to_ws_task.cancel()
        ws_to_channel_task.cancel()
        client.close()


def connect_to_ssh_shell(client: SSHClient, tcp_ip: str, tcp_port: int, pkey: PKey):
    client.connect(tcp_ip, tcp_port, "root", pkey=pkey, timeout=30)
    return client.invoke_shell()


@router.get("/testSession")
def test_session(session: SessionAD):
    session
    return {"message": "session is valid"}
