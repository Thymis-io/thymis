import datetime
import logging
import os
import pathlib
from typing import Annotated, Dict, Generator
import uuid
from typing import Annotated, Dict, Optional, Union

from pydantic import BaseModel
from sqlalchemy.orm import Session
from thymis_controller.database import engine

logger = logging.getLogger(__name__)


from fastapi import Cookie, Depends, HTTPException, Request, Response, WebSocket, status
from thymis_controller.config import global_settings
from thymis_controller.project import Project

global_project = None


def get_project():
    global global_project
    if global_project is None:
        REPO_PATH = global_settings.REPO_PATH.resolve()

        global_project = Project(REPO_PATH)
    return global_project


def get_state(project: Project = Depends(get_project)):
    return project.read_state()


class SessionTicket(BaseModel):
    created: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    token: str | None


SESSION_STORE: Dict[uuid.UUID, SessionTicket] = {}
SESSION_LIFETIME = datetime.timedelta(days=1)


def get_session(session):
    session = uuid.UUID(session) if session else None
    if session is None:
        return None
    session_ticket = SESSION_STORE.get(session)
    if session_ticket is None:
        return None
    if session_ticket.created + SESSION_LIFETIME < datetime.datetime.now(
        datetime.timezone.utc
    ):
        del SESSION_STORE[session]
        return None
    return session_ticket


def require_valid_session(session: Annotated[Union[str, None], Cookie()] = None):
    """
    Check if the session is valid
    """
    session = get_session(session)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No valid session"
        )
    return session


def invalidate_session(response: Response):
    response.delete_cookie("session")
    return


def apply_session(response: Response, token: str):
    session_ticket = SessionTicket(token=token)
    session_id = uuid.uuid4()
    SESSION_STORE[session_id] = session_ticket
    response.set_cookie(key="session", value=str(session_id), httponly=False, samesite='strict', expires=session_ticket.created + SESSION_LIFETIME)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

# session annotated dependency for FastAPI endpoints
SessionAD = Annotated[Session, Depends(get_session)]
