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


def update_project_state(
    new_state: State,
    project,
    db_session,
    network_relay,
    background_tasks: BackgroundTasks,
) -> None:
    """Apply a validated state replacement with the device-type safety gate."""
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


def _decode_json_pointer_token(token: str) -> str:
    index = 0
    while index < len(token):
        if token[index] == "~":
            if index + 1 == len(token) or token[index + 1] not in "01":
                raise HTTPException(
                    status_code=400, detail="Invalid JSON Pointer escape"
                )
            index += 2
        else:
            index += 1
    return token.replace("~1", "/").replace("~0", "~")


def _list_index(token: str, length: int, *, allow_append: bool = False) -> int:
    if allow_append and token == "-":
        return length
    if not token.isdecimal():
        raise HTTPException(
            status_code=400, detail="Expected a JSON Pointer array index"
        )
    index = int(token)
    if index >= length:
        raise HTTPException(
            status_code=400, detail="JSON Pointer array index is out of range"
        )
    return index


def apply_config_field_patch(document: dict, patch: models.ConfigFieldPatch) -> None:
    """Mutate a JSON-compatible configuration document using an RFC 6901 pointer."""
    tokens = [_decode_json_pointer_token(token) for token in patch.path[1:].split("/")]
    parent: dict | list = document
    for token in tokens[:-1]:
        if isinstance(parent, dict):
            if token not in parent:
                raise HTTPException(
                    status_code=404, detail="JSON Pointer path not found"
                )
            parent = parent[token]
        elif isinstance(parent, list):
            parent = parent[_list_index(token, len(parent))]
        else:
            raise HTTPException(
                status_code=400, detail="JSON Pointer path is not a container"
            )

    token = tokens[-1]
    if isinstance(parent, dict):
        if patch.operation == "remove":
            if token not in parent:
                raise HTTPException(
                    status_code=404, detail="JSON Pointer path not found"
                )
            del parent[token]
        else:
            parent[token] = patch.value
        return

    if isinstance(parent, list):
        index = _list_index(token, len(parent), allow_append=patch.operation == "set")
        if patch.operation == "remove":
            del parent[index]
        elif index == len(parent):
            parent.append(patch.value)
        else:
            parent[index] = patch.value
        return

    raise HTTPException(status_code=400, detail="JSON Pointer path is not a container")


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
    update_project_state(
        new_state,
        project,
        db_session,
        network_relay,
        background_tasks,
    )
    return new_state


@router.get("/configs/{config_identifier}", response_model=Config)
def get_config(config_identifier: str, project: ProjectAD):
    """Return one configuration without requiring clients to parse global state."""
    config = next(
        (
            config
            for config in project.read_state().configs
            if config.identifier == config_identifier
        ),
        None,
    )
    if config is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@router.patch("/configs/{config_identifier}/field", response_model=Config)
def patch_config_field(
    config_identifier: str,
    patch: models.ConfigFieldPatch,
    project: ProjectAD,
    db_session: DBSessionAD,
    network_relay: NetworkRelayAD,
    background_tasks: BackgroundTasks,
):
    """Atomically apply one JSON Pointer mutation to one configuration."""
    new_state = project.read_state().model_copy(deep=True)
    config_index = next(
        (
            index
            for index, config in enumerate(new_state.configs)
            if config.identifier == config_identifier
        ),
        None,
    )
    if config_index is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    config_payload = new_state.configs[config_index].model_dump(mode="json")
    apply_config_field_patch(config_payload, patch)
    updated_config = Config.model_validate(config_payload)
    new_state.configs[config_index] = updated_config
    update_project_state(
        new_state,
        project,
        db_session,
        network_relay,
        background_tasks,
    )
    return updated_config


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
