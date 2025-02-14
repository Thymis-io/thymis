import uuid

from sqlalchemy.orm import Session
from thymis_controller import db_models


def create(
    session: Session,
    original_disk_config_commit: str,
    original_disk_config_id: str,
    token: str,
) -> db_models.AgentToken:
    new_agent_token = db_models.AgentToken(
        original_disk_config_commit=original_disk_config_commit,
        original_disk_config_id=original_disk_config_id,
        token=token,
    )
    session.add(new_agent_token)
    session.commit()
    session.refresh(new_agent_token)
    return new_agent_token


def check_token_validity(session: Session, token: str) -> bool:
    return (
        session.query(db_models.AgentToken)
        .filter_by(token=token, revoked=False)
        .count()
        > 0
    )


def create_access_client_token(
    session: Session,
    deployment_info_id: uuid.UUID,
    token: str,
    deploy_device_task_id: uuid.UUID,
) -> db_models.AccessClientToken:
    new_access_client_token = db_models.AccessClientToken(
        token=token,
        for_deployment_info_id=deployment_info_id,
        deploy_device_task_id=deploy_device_task_id,
    )
    session.add(new_access_client_token)
    session.commit()
    session.refresh(new_access_client_token)
    return new_access_client_token


def check_access_client_token_validity(
    session: Session, token: str, deployment_info_id: str
) -> bool:
    return (
        session.query(db_models.AccessClientToken)
        .filter_by(
            token=token,
            revoked=False,
            for_deployment_info_id=uuid.UUID(deployment_info_id),
        )
        .count()
        > 0
    )


def revoke_access_client_token(session: Session, token: str):
    session.query(db_models.AccessClientToken).filter_by(token=token).update(
        {"revoked": True}
    )
    session.commit()
