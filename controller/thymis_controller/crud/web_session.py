import datetime
import uuid

import thymis_controller.db_models as db_models
from sqlalchemy.orm import Session

SESSION_LIFETIME = datetime.timedelta(days=1)


def create(db_session: Session) -> db_models.WebSession:
    session_id = uuid.uuid4()
    created_at = datetime.datetime.now(datetime.timezone.utc)
    web_session = db_models.WebSession(
        session_id=str(session_id), created_at=created_at, updated_at=created_at
    )
    db_session.add(web_session)
    db_session.commit()
    return web_session


def validate(db_session: Session, session_id: uuid.UUID):
    web_session = (
        db_session.query(db_models.WebSession)
        .filter_by(session_id=str(session_id))
        .first()
    )

    if web_session is None:
        return False

    # TODO delete expired sessions
    return (
        web_session.created_at.astimezone(datetime.timezone.utc) + SESSION_LIFETIME
    ) > datetime.datetime.now(datetime.timezone.utc)


def delete(db_session: Session, session_id: uuid.UUID):
    db_session.query(db_models.WebSession).filter_by(session_id=session_id).delete()
    db_session.commit()
