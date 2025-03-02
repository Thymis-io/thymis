from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, Request
from thymis_controller import dependencies, models, modules
from thymis_controller.dependencies import ProjectAD
from thymis_controller.models.state import State

router = APIRouter()


@router.get("/state")
def get_state(state: State = Depends(dependencies.get_state)):
    return state


@router.patch("/state")
def update_state(payload: Annotated[dict, Body()], project: ProjectAD):
    new_state = State.model_validate(payload)
    project.write_state_and_reload(new_state)
    return new_state


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


@router.get("/history/diff", tags=["history"])
def get_diff(
    project: ProjectAD,
    refA: Optional[str] = "",
    refB: Optional[str] = "",
):
    return project.repo.diff(refA, refB)


@router.get("/repo_status", tags=["history"])
def get_repo_status(project: ProjectAD):
    return project.repo.status()


@router.get("/available_modules")
def get_available_modules(request: Request) -> list[models.Module]:
    locale = request.cookies.get("locale", "en")
    return [module.get_model(locale) for module in modules.ALL_MODULES]
