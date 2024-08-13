import datetime
import uuid

from thymis_controller import models
from thymis_controller import dependencies
from thymis_controller.dependencies import SessionAD


def create(session: SessionAD):
    session_id = uuid.uuid4()
    web_session = models.WebSession(session_id=session_id)
    session.add(web_session)
    session.commit()
    return web_session

def validate(session: SessionAD, session_id: uuid.UUID):
    web_session = session.query(models.WebSession).filter_by(session_id=session_id).first()

    if web_session is None:
        return False
    
    # currently we keep the expired sessions in the database for tracking purposes
    return web_session.created + dependencies.SESSION_LIFETIME < datetime.datetime.now(datetime.timezone.utc)
