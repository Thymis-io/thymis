from fastapi import APIRouter, BackgroundTasks, Depends, Request, WebSocket
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from thymis_controller import dependencies, models, modules, project, task
from thymis_controller.dependencies import get_project
from thymis_controller.models.state import State

router = APIRouter()


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
def build_repo(
    background_tasks: BackgroundTasks, project: project.Project = Depends(get_project)
):
    # runs a nix command to build the flake
    background_tasks.add_task(project.create_build_task())
    # now build_nix: type: BackgroundTasks -> None

    return {"message": "nix build started"}


@router.websocket("/task_status")
async def task_status(websocket: WebSocket):
    await task.connection_manager.connect(websocket)


@router.post("/action/deploy")
def deploy(
    summary: str,
    background_tasks: BackgroundTasks,
    project: project.Project = Depends(get_project),
):
    project.commit(summary)

    # runs a nix command to deploy the flake
    background_tasks.add_task(project.create_deploy_project_task())

    return {"message": "nix deploy started"}


@router.post("/action/build-download-image")
def build_download_image(
    identifier: str,
    background_tasks: BackgroundTasks,
    project: project.Project = Depends(get_project),
):
    background_tasks.add_task(project.create_build_device_image_task(identifier))


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
    background_tasks: BackgroundTasks,
    project: project.Project = Depends(get_project),
):
    project.write_state_and_reload(project.read_state())
    background_tasks.add_task(project.create_update_task())
    return {"message": "update started"}
