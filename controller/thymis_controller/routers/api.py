from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import FileResponse, RedirectResponse
from thymis_controller import dependencies, models, modules, project
from thymis_controller.dependencies import get_project
from thymis_controller.models.state import State
from thymis_controller.routers import task

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


@router.post("/history/revert-commit")
def revert_commit(
    commit_sha: str,
    project: project.Project = Depends(get_project),
):
    project.revert_commit(commit_sha)
    return {"message": "reverted commit"}


@router.post("/action/update")
async def update(
    project: project.Project = Depends(get_project),
):
    project.write_state_and_reload(project.read_state())
    await project.create_update_task()
    return {"message": "update started"}
