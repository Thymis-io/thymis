import asyncio
import os
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, RedirectResponse
from paramiko import PKey, SSHClient
from thymis_controller import crud, dependencies, models, modules, utils
from thymis_controller.config import global_settings
from thymis_controller.dependencies import (
    ProjectAD,
    SessionAD,
    TaskControllerAD,
    require_valid_user_session,
)
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

    task_controller.submit(
        models.DeployDevicesTaskSubmission(
            devices=devices,
            project_path=str(project.path),
            ssh_key_path=str(global_settings.SSH_KEY_PATH),
            known_hosts_path=str(project.known_hosts_path),
        ),
        db_session=session,
    )

    return {"message": "nix deploy started"}


@router.post("/action/build-download-image")
async def build_download_image(
    identifier: str,
    db_session: SessionAD,
    project: ProjectAD,
):
    await project.create_build_device_image_task(identifier, db_session)


@router.post("/action/build-download-image-for-clone")
async def device_and_build_download_image_for_clone(
    identifier: str,
    db_session: SessionAD,
    project: ProjectAD,
):
    state = project.read_state()
    x = 1
    device_name = lambda x: f"{identifier}-{x}"
    check_name = lambda x: any(
        device.identifier == device_name(x) for device in state.devices
    )
    while check_name(x):
        x += 1

    new_identifier = device_name(x)
    project.clone_state_device(identifier, new_identifier, lambda n: f"{n}-{x}")
    await project.create_build_device_image_task(new_identifier, db_session)


@router.post("/action/restart-device")
async def restart_device(
    identifier: str,
    db_session: SessionAD,
    task_controller: TaskControllerAD,
    project: ProjectAD,
):
    target_host = crud.deployment_info.get_device_host_by_config_id(
        db_session, identifier
    )
    task_controller.submit(
        models.SSHCommandTaskSubmission(
            target_host=target_host,
            target_user="root",
            target_port=22,
            command="reboot",
            ssh_key_path=str(global_settings.SSH_KEY_PATH),
            ssh_known_hosts_path=str(project.known_hosts_path),
        ),
        db_session=db_session,
    )


@router.get("/download-image")
def download_image(
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
                return FileResponse(os.path.join(root, file))

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


@router.websocket("/vnc/{identifier}")
async def vnc_websocket(
    identifier: str,
    db_session: SessionAD,
    websocket: WebSocket,
    state: State = Depends(dependencies.get_state),
):
    device = next(device for device in state.devices if device.identifier == identifier)
    target_host = crud.deployment_info.get_device_host_by_config_id(
        db_session, identifier
    )

    if device is None or target_host is None:
        await websocket.close()
        return

    await websocket.accept()

    tcp_ip = target_host
    tcp_port = 5900
    tcp_reader, tcp_writer = await asyncio.open_connection(tcp_ip, tcp_port)

    tcp_to_ws_task = asyncio.create_task(tcp_to_websocket(tcp_reader, websocket))
    ws_to_tcp_task = asyncio.create_task(websocket_to_tcp(tcp_writer, websocket))

    try:
        await asyncio.gather(tcp_to_ws_task, ws_to_tcp_task)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        tcp_to_ws_task.cancel()
        ws_to_tcp_task.cancel()


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


@router.websocket("/terminal/{identifier}")
async def terminal_websocket(
    identifier: str,
    db_session: SessionAD,
    websocket: WebSocket,
    project: ProjectAD,
    state: State = Depends(dependencies.get_state),
):
    device = next(device for device in state.devices if device.identifier == identifier)
    target_host = crud.deployment_info.get_device_host_by_config_id(
        db_session, identifier
    )

    if device is None or target_host is None:
        await websocket.close()
        return

    await websocket.accept()

    tcp_ip = target_host
    tcp_port = 22

    client = SSHClient()
    client.load_host_keys(project.known_hosts_path)
    pkey: PKey = PKey.from_path(global_settings.SSH_KEY_PATH)

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
