import logging
import os
import uuid

from fastapi import APIRouter, HTTPException
from thymis_controller import crud, models
from thymis_controller.dependencies import DBSessionAD, NetworkRelayAD, ProjectAD
from thymis_controller.models import device

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/deployment_infos_by_config_id/{deployed_config_id}",
    response_model=list[device.DeploymentInfo],
)
def get_deployment_infos_by_config_id(db_session: DBSessionAD, deployed_config_id: str):
    """
    Gets the deployment infos for all devices with the given deployed_config_id
    """
    return map(
        device.DeploymentInfo.from_deployment_info,
        crud.deployment_info.get_by_config_id(db_session, deployed_config_id),
    )


@router.get(
    "/connected_deployment_infos_by_config_id/{deployed_config_id}",
    response_model=list[device.DeploymentInfo],
)
def get_connected_deployment_infos_by_config_id(
    db_session: DBSessionAD, deployed_config_id: str, network_relay: NetworkRelayAD
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
        device.DeploymentInfo.from_deployment_info,
        connected_deployment_infos,
    )


@router.get("/deployment_info/{id}", response_model=models.DeploymentInfo)
def get_deployment_info(db_session: DBSessionAD, id: uuid.UUID):
    """
    Get a specific deployment_info by id
    """
    deployment_info = crud.deployment_info.get_by_id(db_session, id)
    if not deployment_info:
        raise HTTPException(status_code=404, detail="Deployment info not found")
    return deployment_info


@router.delete("/deployment_info/{id}", status_code=204)
def delete_deployment_info(db_session: DBSessionAD, id: uuid.UUID, project: ProjectAD):
    """
    Delete a deployment_info
    """
    crud.deployment_info.delete(db_session, id)
    project.update_known_hosts(db_session)


@router.get(
    "/all_connected_deployment_info", response_model=list[models.DeploymentInfo]
)
def get_connected_deployment_infos(
    db_session: DBSessionAD, network_relay: NetworkRelayAD
):
    """
    Get all connected deployment_infos
    """
    all_deployment_infos = crud.deployment_info.get_all_stable(db_session)
    connected_deployment_infos = []
    for deployment_info in all_deployment_infos:
        if network_relay.public_key_to_connection_id.get(
            deployment_info.ssh_public_key
        ):
            connected_deployment_infos.append(deployment_info)
    return map(
        models.DeploymentInfo.from_deployment_info,
        connected_deployment_infos,
    )


@router.get("/all_deployment_infos", response_model=list[models.DeploymentInfo])
def get_all_deployment_infos(db_session: DBSessionAD):
    """
    Get all deployment_infos
    """
    return map(
        models.DeploymentInfo.from_deployment_info,
        crud.deployment_info.get_all(db_session),
    )


@router.patch("/deployment_info/{id}", response_model=models.DeploymentInfo)
def update_deployment_info(
    db_session: DBSessionAD,
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


if "RUNNING_IN_PLAYWRIGHT" in os.environ:

    @router.post("/create_deployment_info", response_model=models.DeploymentInfo)
    def create_deployment_info(
        db_session: DBSessionAD,
        deployment_info: models.CreateDeploymentInfoLegacyHostkeyRequest,
        project: ProjectAD,
    ):
        result = crud.deployment_info.create(
            db_session,
            ssh_public_key=deployment_info.ssh_public_key,
            deployed_config_id=deployment_info.deployed_config_id,
            reachable_deployed_host=deployment_info.reachable_deployed_host,
        )
        project.update_known_hosts(db_session)
        return models.DeploymentInfo.from_deployment_info(result)


@router.get("/hardware_device", response_model=list[models.HardwareDevice])
def get_hardware_devices(db_session: DBSessionAD):
    """
    Get all hardware devices
    """
    return crud.hardware_device.get_all(db_session)
