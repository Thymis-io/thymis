import os
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import nullslast
from sqlalchemy.orm import Session
from thymis_controller import db_models

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
) -> db_models.DeploymentInfo:
    deployment_info = (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.id == id)
        .first()
    )
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
    session.commit()
    session.refresh(deployment_info)
    return deployment_info


def create_or_update_by_public_key(
    session: Session,
    ssh_public_key: str,
    deployed_config_id: str,
    reachable_deployed_host: str | None = None,
) -> db_models.DeploymentInfo:
    deployment_info = (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.ssh_public_key == ssh_public_key)
        .first()
    )
    if deployment_info:
        return update(
            session,
            deployment_info.id,
            ssh_public_key,
            deployed_config_commit=None,
            deployed_config_id=deployed_config_id,
            reachable_deployed_host=reachable_deployed_host,
            last_seen=datetime.now(timezone.utc),
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


def get_connected_deployment_infos(db_session: Session, network_relay: "NetworkRelay"):
    return [
        deployment_info
        for deployment_info in get_all_stable(db_session)
        if network_relay.public_key_to_connection_id.get(deployment_info.ssh_public_key)
    ]


if "RUNNING_IN_PLAYWRIGHT" in os.environ:

    def delete_all(session: Session):
        session.query(db_models.DeploymentInfo).delete()
        session.commit()
