from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request
from thymis_controller import crud, dependencies, models, modules
from thymis_controller.dependencies import DBSessionAD, NetworkRelayAD, ProjectAD
from thymis_controller.models.state import Config, State
from thymis_controller.repo import RepoStatus

router = APIRouter()


def changed_device_type_configs(old_state: State, new_state: State) -> list[Config]:
    old_configs = {config.identifier: config for config in old_state.configs}
    changed_configs = []

    for new_config in new_state.configs:
        old_config = old_configs.get(new_config.identifier)
        if old_config and old_config.device_type() != new_config.device_type():
            changed_configs.append(new_config)

    return changed_configs


@router.get("/state")
def get_state(state: State = Depends(dependencies.get_state)):
    return state


@router.patch("/state")
def update_state(
    payload: Annotated[dict, Body()],
    project: ProjectAD,
    db_session: DBSessionAD,
    network_relay: NetworkRelayAD,
    background_tasks: BackgroundTasks,
):
    new_state = State.model_validate(payload)
    for config in changed_device_type_configs(project.read_state(), new_state):
        connected_devices = [
            deployment_info
            for deployment_info in crud.deployment_info.get_by_config_id(
                db_session, config.identifier
            )
            if network_relay.public_key_to_connection_id.get(
                deployment_info.ssh_public_key
            )
        ]
        if connected_devices:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change device type for config '{config.identifier}' while devices are connected",
            )
    project.write_state(new_state)
    background_tasks.add_task(project.reload_state, new_state)
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


last_known_repo_status = RepoStatus(changes=[])


@router.get("/repo_status", tags=["history"])
def get_repo_status(project: ProjectAD):
    global last_known_repo_status
    # try to acquire the lock for a short time to avoid blocking for too long
    if project.write_repo_lock.acquire(timeout=0.3):
        try:
            last_known_repo_status = project.repo.status()
        finally:
            project.write_repo_lock.release()
    return last_known_repo_status


@router.get("/available_modules")
def get_available_modules(request: Request) -> list[models.Module]:
    locale = request.cookies.get("locale", "en")
    return [module.get_model(locale) for module in modules.ALL_MODULES]
