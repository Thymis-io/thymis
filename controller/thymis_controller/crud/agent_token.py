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
