import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

import thymis_controller.crud.agent_connection as crud_agent_connection
import thymis_controller.crud.device_metric as crud_device_metric
import thymis_controller.crud.logs as crud_logs
from fastapi import APIRouter, HTTPException, Query
from thymis_controller import crud, db_models, models
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
    return map(
        models.DeploymentInfo.from_deployment_info,
        crud.deployment_info.get_connected_deployment_infos(db_session, network_relay),
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
    deployment_info: models.UpdateDeploymentInfo,
    project: ProjectAD,
):
    """
    Update a deployment_info
    """
    fields = {}
    if "ssh_public_key" in deployment_info.model_fields_set:
        fields["ssh_public_key"] = deployment_info.ssh_public_key
    if "deployed_config_id" in deployment_info.model_fields_set:
        fields["deployed_config_id"] = deployment_info.deployed_config_id
    if "reachable_deployed_host" in deployment_info.model_fields_set:
        fields["reachable_deployed_host"] = deployment_info.reachable_deployed_host
    if "name" in deployment_info.model_fields_set:
        fields["name"] = deployment_info.name
    if "location" in deployment_info.model_fields_set:
        fields["location"] = deployment_info.location
    result = crud.deployment_info.update(db_session, id, **fields)
    if not result:
        raise HTTPException(status_code=404, detail="Deployment info not found")
    # SSH-related field changes require rebuilding known_hosts.
    if (
        "ssh_public_key" in deployment_info.model_fields_set
        or "reachable_deployed_host" in deployment_info.model_fields_set
    ):
        project.update_known_hosts(db_session)
    return result


if "RUNNING_IN_PLAYWRIGHT" in os.environ:

    @router.post("/create_deployment_info", response_model=models.DeploymentInfo)
    def create_deployment_info(
        db_session: DBSessionAD,
        deployment_info: models.UpdateDeploymentInfo,
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


class MetricGranularity(str, Enum):
    one_min = "1min"
    fifteen_min = "15min"
    one_hour = "1h"


@router.get("/deployment_info/{id}/connection_history")
def get_connection_history(id: uuid.UUID, db_session: DBSessionAD) -> list:
    """Get the last 10 connection events for a device."""
    connections = crud_agent_connection.get_by_deployment_info(db_session, id)
    return [
        {
            "connected_at": conn.connected_at,
            "disconnected_at": conn.disconnected_at,
            "duration_seconds": (
                (conn.disconnected_at - conn.connected_at).total_seconds()
                if conn.disconnected_at
                else None
            ),
        }
        for conn in connections
    ]


@router.get("/deployment_info/{id}/metrics")
def get_device_metrics(
    id: uuid.UUID,
    db_session: DBSessionAD,
    hours: int = Query(default=168, ge=1, le=168),
    granularity: MetricGranularity = Query(default=MetricGranularity.one_hour),
) -> list:
    """Get downsampled device metrics for the past N hours."""
    now = datetime.now(timezone.utc)
    from_time = now - timedelta(hours=hours)
    return crud_device_metric.get_metrics_downsampled(
        db_session, id, from_time, now, granularity.value
    )


@router.get("/deployment_info/{id}/error_logs")
def get_error_logs(id: uuid.UUID, db_session: DBSessionAD) -> list:
    """Get the last 50 Error/Critical log entries for a device."""
    deployment_info = db_session.get(db_models.DeploymentInfo, id)
    if deployment_info is None:
        raise HTTPException(status_code=404, detail="Device not found")
    log_list = crud_logs.get_logs(
        db_session,
        deployment_info,
        limit=50,
        max_severity=3,  # syslog: 0=Emergency, 1=Alert, 2=Critical, 3=Error
    )
    return [log.model_dump() for log in log_list.logs]
