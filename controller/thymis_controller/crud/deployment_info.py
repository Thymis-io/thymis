import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import nullslast
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.orm import Session
from thymis_controller import db_models

# Sentinel distinguishing "caller passed no value" from "caller explicitly passed None".
# Required for update() fields that are nullable: None must mean "set to NULL",
# not "leave unchanged" (which is what None means for the other update() params).
_UNSET = object()

if TYPE_CHECKING:
    from thymis_controller.network_relay import NetworkRelay


def create(
    session: Session,
    ssh_public_key: str,
    deployed_config_commit: str | None = None,
    deployed_config_id: str | None = None,
    reachable_deployed_host: str | None = None,
) -> db_models.DeploymentInfo:
    new_deployment_info = db_models.DeploymentInfo(
        ssh_public_key=ssh_public_key,
        deployed_config_commit=deployed_config_commit,
        deployed_config_id=deployed_config_id,
        reachable_deployed_host=reachable_deployed_host,
        last_seen=datetime.now(timezone.utc),
        first_seen=datetime.now(timezone.utc),
    )
    session.add(new_deployment_info)
    session.commit()
    session.refresh(new_deployment_info)
    return new_deployment_info


def update(
    session: Session,
    id: uuid.UUID,
    ssh_public_key: str | None = None,
    deployed_config_commit: str | None = None,
    deployed_config_id: str | None = None,
    reachable_deployed_host: str | None = None,
    last_seen: str | None = None,
    archived: bool | None = None,
    network_interfaces: list | None = None,
    location: str | None = _UNSET,
    name: str | None = _UNSET,
    pending_config_id: str | None = _UNSET,
    ram_bytes: int | None = None,
    notes: str | None = _UNSET,
    image_update_state: dict | None = _UNSET,
    pending_image_version: str | None = _UNSET,
    pending_image_task_id: uuid.UUID | None = _UNSET,
    pending_image_config_id: str | None = _UNSET,
    pending_image_config_commit: str | None = _UNSET,
) -> db_models.DeploymentInfo | None:
    deployment_info = session.get(db_models.DeploymentInfo, id)
    if deployment_info is None:
        return None
    if ssh_public_key is not None:
        deployment_info.ssh_public_key = ssh_public_key
    if deployed_config_commit is not None:
        deployment_info.deployed_config_commit = deployed_config_commit
    if deployed_config_id is not None:
        deployment_info.deployed_config_id = deployed_config_id
    if reachable_deployed_host is not None:
        deployment_info.reachable_deployed_host = reachable_deployed_host
    if last_seen is not None:
        deployment_info.last_seen = last_seen
    if deployment_info.first_seen is None:
        deployment_info.first_seen = last_seen
    if archived is not None:
        deployment_info.archived = archived
    if network_interfaces is not None:
        deployment_info.network_interfaces = network_interfaces
    if location is not _UNSET:
        deployment_info.location = location
    if name is not _UNSET:
        deployment_info.name = name
    if pending_config_id is not _UNSET:
        deployment_info.pending_config_id = pending_config_id
    if ram_bytes is not None:
        deployment_info.ram_bytes = ram_bytes
    if notes is not _UNSET:
        deployment_info.notes = notes
    if image_update_state is not _UNSET:
        deployment_info.image_update_state = image_update_state
    if pending_image_version is not _UNSET:
        deployment_info.pending_image_version = pending_image_version
    if pending_image_task_id is not _UNSET:
        deployment_info.pending_image_task_id = pending_image_task_id
    if pending_image_config_id is not _UNSET:
        deployment_info.pending_image_config_id = pending_image_config_id
    if pending_image_config_commit is not _UNSET:
        deployment_info.pending_image_config_commit = pending_image_config_commit
    session.commit()
    session.refresh(deployment_info)
    return deployment_info


def reserve_image_update(
    session: Session,
    deployment_info_id: uuid.UUID,
    task_id: uuid.UUID,
    pending_config_id: str | None = None,
) -> bool:
    """Reserve a device for one image deployment task."""
    result = session.execute(
        sqlalchemy_update(db_models.DeploymentInfo)
        .where(
            db_models.DeploymentInfo.id == deployment_info_id,
            db_models.DeploymentInfo.pending_image_task_id.is_(None),
        )
        .values(
            pending_image_task_id=task_id,
            pending_config_id=pending_config_id,
        )
    )
    session.commit()
    return result.rowcount == 1


def set_pending_image_update(
    session: Session,
    deployment_info_id: uuid.UUID,
    task_id: uuid.UUID,
    *,
    version: str,
    config_id: str,
    config_commit: str,
) -> bool:
    """Record staged metadata only when the task still owns the reservation."""
    result = session.execute(
        sqlalchemy_update(db_models.DeploymentInfo)
        .where(
            db_models.DeploymentInfo.id == deployment_info_id,
            db_models.DeploymentInfo.pending_image_task_id == task_id,
        )
        .values(
            pending_image_version=version,
            pending_image_config_id=config_id,
            pending_image_config_commit=config_commit,
        )
    )
    session.commit()
    return result.rowcount == 1


def clear_pending_image_update(
    session: Session, deployment_info_id: uuid.UUID, task_id: uuid.UUID
) -> bool:
    """Clear pending metadata only when the task still owns the reservation."""
    result = session.execute(
        sqlalchemy_update(db_models.DeploymentInfo)
        .where(
            db_models.DeploymentInfo.id == deployment_info_id,
            db_models.DeploymentInfo.pending_image_task_id == task_id,
        )
        .values(
            pending_config_id=None,
            pending_image_version=None,
            pending_image_task_id=None,
            pending_image_config_id=None,
            pending_image_config_commit=None,
        )
    )
    session.commit()
    return result.rowcount == 1


def complete_pending_image_update(
    session: Session,
    deployment_info_id: uuid.UUID,
    task_id: uuid.UUID,
    *,
    deployed_config_id: str,
    deployed_config_commit: str,
) -> bool:
    """Commit a reported image only when the task still owns the reservation."""
    result = session.execute(
        sqlalchemy_update(db_models.DeploymentInfo)
        .where(
            db_models.DeploymentInfo.id == deployment_info_id,
            db_models.DeploymentInfo.pending_image_task_id == task_id,
        )
        .values(
            deployed_config_id=deployed_config_id,
            deployed_config_commit=deployed_config_commit,
            pending_config_id=None,
            pending_image_version=None,
            pending_image_task_id=None,
            pending_image_config_id=None,
            pending_image_config_commit=None,
        )
    )
    session.commit()
    return result.rowcount == 1


def _latest_completed_switch_for_deployment_info(
    session: Session, deployment_info_id: uuid.UUID
) -> tuple[str, str] | None:
    recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    tasks = (
        session.query(db_models.Task)
        .filter(
            db_models.Task.task_type == "deploy_device_task",
            db_models.Task.state == "completed",
            db_models.Task.end_time >= recent_cutoff,
        )
        .order_by(db_models.Task.start_time.desc())
        .limit(50)
        .all()
    )
    for task in tasks:
        task_data = task.task_submission_data or {}
        device = task_data.get("device", {})
        if device.get("deployment_info_id") != str(deployment_info_id):
            continue
        source_identifier = device.get("source_identifier")
        target_identifier = device.get("identifier")
        if source_identifier and target_identifier:
            return source_identifier, target_identifier
    return None


def create_or_update_by_public_key(
    session: Session,
    ssh_public_key: str,
    deployed_config_id: str,
    reachable_deployed_host: str | None = None,
    network_interfaces: list | None = None,
    *,
    preserve_confirmed_switch: bool = False,
) -> db_models.DeploymentInfo:
    deployment_info = (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.ssh_public_key == ssh_public_key)
        .first()
    )
    if deployment_info:
        effective_deployed_config_id = deployed_config_id
        if preserve_confirmed_switch and deployment_info.pending_config_id is None:
            latest_switch = _latest_completed_switch_for_deployment_info(
                session, deployment_info.id
            )
            if latest_switch is not None:
                source_identifier, target_identifier = latest_switch
                if deployed_config_id == source_identifier:
                    effective_deployed_config_id = target_identifier

        return update(
            session,
            deployment_info.id,
            ssh_public_key,
            deployed_config_commit=None,
            deployed_config_id=effective_deployed_config_id,
            reachable_deployed_host=reachable_deployed_host,
            last_seen=datetime.now(timezone.utc),
            network_interfaces=network_interfaces,
        )
    return create(
        session,
        ssh_public_key,
        deployed_config_commit=None,
        deployed_config_id=deployed_config_id,
        reachable_deployed_host=reachable_deployed_host,
    )


def get_by_id(session: Session, id: str) -> db_models.DeploymentInfo | None:
    return (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.id == id)
        .first()
    )


def delete(session: Session, id: str) -> None:
    session.query(db_models.DeploymentInfo).filter(
        db_models.DeploymentInfo.id == id
    ).delete()
    session.commit()


def get_by_ssh_public_key(
    session: Session, ssh_public_key: str
) -> list[db_models.DeploymentInfo]:
    return (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.ssh_public_key == ssh_public_key)
        .all()
    )


def check_if_ssh_public_key_exists(session: Session, ssh_public_key: str) -> bool:
    return (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.ssh_public_key == ssh_public_key)
        .first()
        is not None
    )


def get_all(session: Session):
    return (
        session.query(db_models.DeploymentInfo)
        .order_by(db_models.DeploymentInfo.first_seen.desc())
        .order_by(db_models.DeploymentInfo.last_seen.desc())
        .order_by(db_models.DeploymentInfo.deployed_config_id.asc())
        .order_by(nullslast(db_models.DeploymentInfo.deployed_config_commit.asc()))
        .all()
    )


def get_all_stable(session: Session):
    return (
        session.query(db_models.DeploymentInfo)
        .order_by(db_models.DeploymentInfo.deployed_config_id.asc())
        .order_by(nullslast(db_models.DeploymentInfo.deployed_config_commit.asc()))
        .order_by(db_models.DeploymentInfo.first_seen.desc())
        .order_by(db_models.DeploymentInfo.last_seen.desc())
        .all()
    )


def get_first_device_host_by_config_id(session: Session, config_id: str) -> str | None:
    di = (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.deployed_config_id == config_id)
        .first()
    )
    return di.reachable_deployed_host if di else None


def get_first_by_config_id(session: Session, config_id: str):
    return (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.deployed_config_id == config_id)
        .first()
    )


def get_by_config_id(session: Session, config_id: str):
    return (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.deployed_config_id == config_id)
        .all()
    )


if "RUNNING_IN_PLAYWRIGHT" in os.environ:

    def delete_all(session: Session):
        session.query(db_models.DeploymentInfo).delete()
        session.commit()
