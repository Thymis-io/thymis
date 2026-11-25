import secrets
import threading
import uuid
from typing import Optional

from sqlalchemy.orm import Session
from thymis_controller import db_models

# Tokens are long-lived and every log request validates one. Keep the hot set
# in memory; create/revoke update it explicitly, and unknown tokens still hit
# the database.
_valid_token_cache: set[str] = set()
_valid_token_lock = threading.Lock()


def _remember_valid(token: str) -> None:
    with _valid_token_lock:
        _valid_token_cache.add(token)


def _forget(token: str) -> None:
    with _valid_token_lock:
        _valid_token_cache.discard(token)


def is_token_cached_valid(token: str) -> bool:
    with _valid_token_lock:
        return token in _valid_token_cache


def create(
    session: Session,
    original_disk_config_commit: str | None,
    original_disk_config_id: str | None,
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
    _remember_valid(new_agent_token.token)
    return new_agent_token


def check_token_validity(session: Session, token: str) -> bool:
    if is_token_cached_valid(token):
        return True
    valid = get_valid_token(session, token) is not None
    if valid:
        _remember_valid(token)
    return valid


def get_valid_token(session: Session, token: str) -> db_models.AgentToken | None:
    return (
        session.query(db_models.AgentToken)
        .filter_by(token=token, revoked=False)
        .first()
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


def get_or_create_access_client_token(
    session: Session,
    deployment_info_id: uuid.UUID,
    deploy_device_task_id: Optional[uuid.UUID] = None,
) -> db_models.AccessClientToken:
    token = (
        session.query(db_models.AccessClientToken)
        .filter_by(
            for_deployment_info_id=deployment_info_id,
            deploy_device_task_id=deploy_device_task_id,
            revoked=False,
        )
        .first()
    )

    if token is None:
        token = create_access_client_token(
            session,
            deployment_info_id,
            secrets.token_hex(32),
            deploy_device_task_id,
        )

    return token


def revoke_access_client_token(session: Session, token: str):
    session.query(db_models.AccessClientToken).filter_by(token=token).update(
        {"revoked": True}
    )
    session.commit()


def revoke_agent_token(session: Session, token: str):
    session.query(db_models.AgentToken).filter_by(token=token).update({"revoked": True})
    session.commit()
    _forget(token)
