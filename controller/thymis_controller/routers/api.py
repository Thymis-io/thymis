import asyncio
import logging
import re
import traceback
import uuid
from typing import Annotated

import paramiko
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.requests import HTTPConnection
from fastapi.responses import FileResponse, RedirectResponse
from paramiko import PKey, SSHClient
from sqlalchemy.orm import Session
from thymis_controller import crud, dependencies, models, modules, utils
from thymis_controller.config import global_settings
from thymis_controller.db_models.deployment_info import DeploymentInfo
from thymis_controller.dependencies import (
    NetworkRelayAD,
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

logger = logging.getLogger(__name__)

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
    network_relay: NetworkRelayAD,
):
    project.repo.add(".")
    project.repo.commit(summary)

    devices: list[models.DeployDeviceInformation] = []

    for deployment_info in crud.deployment_info.get_all(session):
        if network_relay.public_key_to_connection_id.get(
            deployment_info.ssh_public_key
        ):
            devices.append(
                models.DeployDeviceInformation(
                    identifier=deployment_info.deployed_config_id,
                    deployment_info_id=deployment_info.id,
                    deployment_public_key=deployment_info.ssh_public_key,
                )
            )

    project.update_known_hosts(session)

    task_controller.submit(
        models.DeployDevicesTaskSubmission(
            devices=devices,
            project_path=str(project.path),
            ssh_key_path=str(global_settings.PROJECT_PATH / "id_thymis"),
            known_hosts_path=str(project.known_hosts_path),
            controller_ssh_pubkey=project.public_key,
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
    project.repo.add(".")
    project.repo.commit(f"Build image for {identifier}")

    device = next(
        device
        for device in project.read_state().devices
        if device.identifier == identifier
    )

    task_controller.submit(
        models.BuildDeviceImageTaskSubmission(
            project_path=str(project.path),
            configuration_id=identifier,
            device_state=device.model_dump(mode="json"),
            commit=project.repo.head.object.hexsha,
            controller_ssh_pubkey=project.public_key,
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


@router.head("/download-image")
@router.get("/download-image")
async def download_image(
    identifier: str,
    state: State = Depends(dependencies.get_state),
):
    # downloads /tmp/thymis-devices.{identifier} file from filesystem
    # compare identifier with project first
    device = next(device for device in state.devices if device.identifier == identifier)

    if device is None:
        return Response(status_code=404)

    # files should be in project_path/images/identifier.ENDING
    expected_endings = ["img", "qcow2", "nixos-vm"]
    non_file_endings = ["nixos-vm"]
    image_dir = global_settings.PROJECT_PATH / "images"
    relevant_paths = []
    our_ending = None
    for ending in expected_endings:
        image_path = image_dir / f"{identifier}.{ending}"
        if image_path.exists():
            relevant_paths.append(image_path)
            our_ending = ending
            if ending in non_file_endings:
                return RedirectResponse(url=f"/images/{device.identifier}.{ending}")

    if not relevant_paths:
        return Response(status_code=404)

    if len(relevant_paths) > 1:
        raise ValueError("Multiple images found")

    return FileResponse(
        relevant_paths[0],
        headers={"content-encoding": "none"},
        filename=f"thymis-image-{device.identifier}.{our_ending}",
    )


@router.websocket("/notification")
async def notification_websocket(websocket: WebSocket):
    await websocket.state.notification_manager.connect(websocket)


@router.get("/history", tags=["history"])
def get_history(project: ProjectAD):
    return project.repo.history()


@router.post("/history/revert-commit", tags=["history"])
def revert_commit(
    commit_sha: str,
    project: ProjectAD,
):
    raise NotImplementedError


@router.get("/history/remotes", tags=["history"])
def get_remotes(project: ProjectAD):
    raise NotImplementedError


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
    network_relay: NetworkRelayAD,
):
    deployment_info = crud.deployment_info.get_by_id(db_session, deployment_info_id)

    if deployment_info is None:
        await websocket.close()
        return

    await websocket.accept()

    agent_connection_id = network_relay.public_key_to_connection_id.get(
        deployment_info.ssh_public_key
    )

    if agent_connection_id is None:
        await websocket.close()
        return

    try:
        connection = await network_relay.create_connection_async(
            agent_connection_id, "localhost", 5900, "tcp"
        )
    except Exception:
        await websocket.close()
        return

    tcp_to_ws_task = asyncio.create_task(tcp_to_websocket(connection, websocket))
    ws_to_tcp_task = asyncio.create_task(websocket_to_tcp(connection, websocket))

    try:
        await asyncio.gather(tcp_to_ws_task, ws_to_tcp_task)
    except Exception:
        traceback.print_exc()
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


@router.get(
    "/connected_deployment_infos_by_config_id/{deployed_config_id}",
    response_model=list[device.DeploymentInfo],
)
def get_connected_deployment_infos_by_config_id(
    db_session: SessionAD, deployed_config_id: str, network_relay: NetworkRelayAD
):
    """
    Gets the deployment infos for all connected devices with the given deployed_config_id
    """
    all_deployment_infos = crud.deployment_info.get_by_config_id(
        db_session, deployed_config_id
    )
    connected_deployment_infos = []
    for deployment_info in all_deployment_infos:
        if network_relay.public_key_to_connection_id.get(
            deployment_info.ssh_public_key
        ):
            connected_deployment_infos.append(deployment_info)
    return map(
        lambda x: x.to_dict(),
        connected_deployment_infos,
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


@router.delete("/deployment_info/{id}", status_code=204)
def delete_deployment_info(db_session: SessionAD, id: uuid.UUID, project: ProjectAD):
    """
    Delete a deployment_info
    """
    crud.deployment_info.delete(db_session, id)
    project.update_known_hosts(db_session)


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


@router.get("/hardware_device", response_model=list[models.HardwareDevice])
def get_hardware_devices(db_session: SessionAD):
    """
    Get all hardware devices
    """
    return crud.hardware_device.get_all(db_session)


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
    websocket: WebSocket,
    db_session: SessionAD,
    network_relay: NetworkRelayAD,
):
    deployment_info = crud.deployment_info.get_by_id(db_session, deployment_info_id)

    if deployment_info is None:
        await websocket.close()
        return

    await websocket.accept()

    class ExpectedHostKeyNotFound(Exception):
        pass

    class CheckForExpectedHostKey(paramiko.MissingHostKeyPolicy):
        def __init__(self, expected_key):
            self.expected_key = expected_key

        def missing_host_key(self, client, hostname, key: paramiko.PKey):
            actual_key = f"{key.get_name()} {key.get_base64()}"
            if actual_key != self.expected_key:
                raise ExpectedHostKeyNotFound()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(
        CheckForExpectedHostKey(deployment_info.ssh_public_key)
    )

    pkey: PKey = PKey.from_path(global_settings.PROJECT_PATH / "id_thymis")

    agent_connection_id = network_relay.public_key_to_connection_id.get(
        deployment_info.ssh_public_key
    )

    if agent_connection_id is None:
        await websocket.close()
        return

    try:
        channel = await run_in_threadpool(
            connect_to_ssh_shell,
            client,
            None,
            None,
            await network_relay.create_connection(
                agent_connection_id, "localhost", 22, "tcp"
            ),
            pkey,
        )
    except ExpectedHostKeyNotFound:
        await websocket.send_bytes(b"Host key mismatch")
        await websocket.close()
        client.close()
        return
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


def connect_to_ssh_shell(
    client: SSHClient, tcp_ip: str | None, tcp_port: int | None, sock, pkey: PKey
):
    client.connect(
        hostname=tcp_ip or "localhost",
        port=tcp_port,
        sock=sock,
        username="root",
        pkey=pkey,
        timeout=30,
    )
    return client.invoke_shell()


@router.get("/testSession")
def test_session(session: SessionAD):
    session
    return {"message": "session is valid"}
