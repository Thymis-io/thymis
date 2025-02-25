import datetime
import random
import uuid
from datetime import datetime, timedelta, timezone

import thymis_controller.db_models as db_models
from sqlalchemy.orm import Session

SESSION_LIFETIME = timedelta(days=1)


def create(db_session: Session) -> db_models.WebSession:
    id = uuid.uuid4()
    session_token = random.randbytes(64).hex()
    created_at = datetime.now(timezone.utc)
    web_session = db_models.WebSession(
        id=id, session_token=session_token, created_at=created_at
    )
    db_session.add(web_session)
    db_session.commit()
    return web_session


def validate(db_session: Session, session_id: uuid.UUID, session_token: str) -> bool:
    web_session = (
        db_session.query(db_models.WebSession)
        .filter_by(id=session_id)
        .filter_by(session_token=session_token)
        .first()
    )

    if web_session is None:
        return False

    expiration_time = web_session.created_at.astimezone(timezone.utc) + SESSION_LIFETIME
    is_expired = expiration_time < datetime.now(timezone.utc)
    if is_expired:
        delete(db_session, session_token)
    return not is_expired


def delete(db_session: Session, session_id: uuid.UUID):
    db_session.query(db_models.WebSession).filter_by(id=session_id).delete()
    db_session.commit()
