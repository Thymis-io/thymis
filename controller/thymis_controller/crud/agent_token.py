from sqlalchemy.orm import Session
from thymis_controller import db_models


def create(
    session: Session,
    config_commit: str,
    config_id: str,
    token: str,
) -> db_models.AgentToken:
    new_agent_token = db_models.AgentToken(
        config_commit=config_commit,
        config_id=config_id,
        token=token,
    )
    session.add(new_agent_token)
    session.commit()
    session.refresh(new_agent_token)
    return new_agent_token
