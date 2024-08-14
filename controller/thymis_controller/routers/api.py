import asyncio
from fastapi import APIRouter, Depends, Request, WebSocket
from fastapi.responses import FileResponse, RedirectResponse
from thymis_controller import dependencies, models, modules, project
from thymis_controller.dependencies import SessionAD, get_project, require_valid_user_session
from thymis_controller.models.state import State
from thymis_controller.routers import task
from thymis_controller.tcp_to_ws import tcp_to_websocket, websocket_to_tcp

router = APIRouter(
    dependencies=[Depends(require_valid_user_session)],
)


@router.get("/state")
def get_state(state: State = Depends(dependencies.get_state)):
    return state


@router.get("/available_modules")
def get_available_modules() -> list[models.Module]:
    # return modules.ALL_MODULES
    return [module.get_model() for module in modules.ALL_MODULES]


@router.patch("/state")
async def update_state(
    new_state: Request, project: project.Project = Depends(get_project)
):
    new_state = await new_state.json()
    new_state = State.model_validate(new_state)
    return project.write_state_and_reload(new_state)


@router.post("/action/build")
async def build_repo(project: project.Project = Depends(get_project)):
    # runs a nix command to build the flake
    await project.create_build_task()
    # now build_nix: type: BackgroundTasks -> None

    return {"message": "nix build started"}


router.include_router(task.router)


@router.post("/action/deploy")
async def deploy(
    summary: str,
    project: project.Project = Depends(get_project),
):
    project.commit(summary)

    # runs a nix command to deploy the flake
    await project.create_deploy_project_task()

    return {"message": "nix deploy started"}


@router.post("/action/build-download-image")
async def build_download_image(
    identifier: str,
    project: project.Project = Depends(get_project),
):
    await project.create_build_device_image_task(identifier)


@router.post("/action/restart-device")
async def restart_device(
    identifier: str,
    project: project.Project = Depends(get_project),
):
    await project.create_restart_device_task(identifier)


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

    return FileResponse(f"/tmp/thymis-devices.{device.identifier}")


@router.get("/history")
def get_history(project: project.Project = Depends(get_project)):
    return project.get_history()


@router.post("/action/update")
async def update(
    project: project.Project = Depends(get_project),
):
    project.write_state_and_reload(project.read_state())
    await project.create_update_task()
    return {"message": "update started"}


@router.websocket("/vnc/{identifier}")
async def websocket_endpoint(
    identifier: str,
    websocket: WebSocket,
    state: State = Depends(dependencies.get_state),
):
    device = next(device for device in state.devices if device.identifier == identifier)

    if device is None:
        await websocket.close()
        return

    await websocket.accept()

    tcp_ip = device.targetHost
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


@router.get("/testSession")
def test_session(session: SessionAD):
    session
    return {"message": "session is valid"}
