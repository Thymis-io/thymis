import logging
import random
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse, RedirectResponse
from thymis_agent import agent
from thymis_controller import crud, dependencies, models
from thymis_controller.config import global_settings
from thymis_controller.crud.agent_token import create_access_client_token
from thymis_controller.dependencies import (
    DBSessionAD,
    NetworkRelayAD,
    ProjectAD,
    TaskControllerAD,
    UserSessionIDAD,
)
from thymis_controller.models.state import State

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/action/build")
async def build_repo(
    project: ProjectAD,
    task_controller: TaskControllerAD,
    db_session: DBSessionAD,
    user_session_id: UserSessionIDAD,
):
    task_controller.submit(
        models.BuildProjectTaskSubmission(project_path=str(project.path)),
        user_session_id=user_session_id,
        db_session=db_session,
    )

    return {"message": "command started"}


@router.post("/action/deploy")
async def deploy(
    session: DBSessionAD,
    project: ProjectAD,
    task_controller: TaskControllerAD,
    network_relay: NetworkRelayAD,
    user_session_id: UserSessionIDAD,
    db_session: DBSessionAD,
    configs: list[str] = Query(None, alias="config"),
):
    if project.repo.is_dirty():
        raise HTTPException(
            status_code=409,
            detail="Repository is dirty. Please commit your changes first.",
        )

    devices: list[models.DeployDeviceInformation] = []

    for deployment_info in crud.deployment_info.get_all(session):
        if (
            deployment_info.deployed_config_id in configs
            and network_relay.public_key_to_connection_id.get(
                deployment_info.ssh_public_key
            )
        ):
            state = project.read_state()
            config = next(
                config
                for config in state.configs
                if config.identifier == deployment_info.deployed_config_id
            )
            modules = project.get_modules_for_config(state, config)
            secrets = []
            for module, settings in modules:
                for secret_type, secret in module.register_secret_settings(
                    settings, project
                ):
                    project.get_secret(db_session, uuid.UUID(secret))
                    secrets.append(
                        agent.SecretForDevice(
                            secret_id=secret,
                            path=secret_type.on_device_path,
                            owner=secret_type.on_device_owner,
                            group=secret_type.on_device_group,
                            mode=secret_type.on_device_mode,
                        )
                    )
            devices.append(
                models.DeployDeviceInformation(
                    identifier=deployment_info.deployed_config_id,
                    deployment_info_id=deployment_info.id,
                    deployment_public_key=deployment_info.ssh_public_key,
                    secrets=secrets,
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
            config_commit=project.repo.head_commit(),
        ),
        user_session_id=user_session_id,
        db_session=session,
    )

    return {"message": "nix deploy started"}


@router.post("/action/build-download-image")
def build_download_image(
    identifier: str,
    db_session: DBSessionAD,
    task_controller: TaskControllerAD,
    user_session_id: UserSessionIDAD,
    project: ProjectAD,
):
    if project.repo.is_dirty():
        raise HTTPException(
            status_code=409,
            detail="Repository is dirty. Please commit your changes first.",
        )

    config = next(
        config
        for config in project.read_state().configs
        if config.identifier == identifier
    )

    modules = project.get_modules_for_config(project.read_state(), config)
    secrets = []
    for module, settings in modules:
        for secret_type, secret in module.register_secret_settings(settings, project):
            db_secret = project.get_secret(db_session, uuid.UUID(secret))
            if db_secret.include_in_image and secret_type.on_device_path:
                secrets.append(
                    agent.SecretForDevice(
                        secret_id=secret,
                        path=secret_type.on_device_path,
                        owner=secret_type.on_device_owner,
                        group=secret_type.on_device_group,
                        mode=secret_type.on_device_mode,
                    )
                )

    task_controller.submit(
        models.BuildDeviceImageTaskSubmission(
            project_path=str(project.path),
            configuration_id=identifier,
            config_state=config.model_dump(mode="json"),
            commit=project.repo.head_commit(),
            controller_ssh_pubkey=project.public_key,
            secrets=secrets,
        ),
        user_session_id=user_session_id,
        db_session=db_session,
    )


@router.post("/action/restart-device")
async def restart_device(
    identifier: str,
    db_session: DBSessionAD,
    task_controller: TaskControllerAD,
    network_relay: NetworkRelayAD,
    user_session_id: UserSessionIDAD,
):
    for deployment_info in crud.deployment_info.get_by_config_id(
        db_session, identifier
    ):
        if network_relay.public_key_to_connection_id.get(
            deployment_info.ssh_public_key
        ):
            access_client_token = random.randbytes(32).hex()
            task = task_controller.submit(
                models.SSHCommandTaskSubmission(
                    controller_access_client_endpoint=task_controller.access_client_endpoint,
                    deployment_info_id=deployment_info.id,
                    access_client_token=access_client_token,
                    deployment_public_key=deployment_info.ssh_public_key,
                    ssh_key_path=str(global_settings.PROJECT_PATH / "id_thymis"),
                    target_user="root",
                    target_port=22,
                    command="reboot",
                ),
                user_session_id=user_session_id,
                db_session=db_session,
            )
            create_access_client_token(
                db_session,
                deployment_info_id=deployment_info.id,
                token=access_client_token,
                deploy_device_task_id=task.id,
            )


@router.head("/download-image")
@router.get("/download-image")
async def download_image(
    identifier: str,
    state: State = Depends(dependencies.get_state),
):
    # downloads /tmp/thymis-devices.{identifier} file from filesystem
    # compare identifier with project first
    device = next(
        (device for device in state.configs if device.identifier == identifier),
        None,
    )

    if device is None:
        return Response(status_code=404)

    # files should be in project_path/images/identifier.ENDING
    expected_endings = ["img", "qcow2", "nixos-vm", "iso"]
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


@router.post("/action/commit")
def commit(project: ProjectAD, message: str):
    project.repo.add(".")
    project.repo.commit(message)
    return {"message": "commit successful"}


@router.post("/action/update")
def update(
    project: ProjectAD,
    task_controller: TaskControllerAD,
    db_session: DBSessionAD,
    user_session_id: UserSessionIDAD,
):
    project.reload_from_disk()
    project.create_update_task(task_controller, user_session_id, db_session)

    return {"message": "update started"}
