import datetime
import logging
import threading
import uuid
from typing import Annotated, Generator, Optional, Union

from fastapi.requests import HTTPConnection
from sqlalchemy.orm import Session
from thymis_controller.crud import web_session
from thymis_controller.task.controller import TaskController

logger = logging.getLogger(__name__)


from fastapi import Cookie, Depends, HTTPException, Request, Response, WebSocket, status
from thymis_controller.config import global_settings
from thymis_controller.project import Project

global_project = None
SESSION_LIFETIME = datetime.timedelta(days=1)
project_lock = threading.Lock()


def get_project():
    global global_project

    with project_lock:
        if global_project is None:
            REPO_PATH = global_settings.REPO_PATH.resolve()

            global_project = Project(REPO_PATH, next(get_db_session()))
        return global_project


ProjectAD = Annotated[Project, Depends(get_project)]


def get_state(project: Project = Depends(get_project)):
    return project.read_state()


def get_db_session() -> Generator[Session, None, None]:
    from thymis_controller.database.connection import engine

    with Session(engine) as session:
        yield session


# session annotated dependency for FastAPI endpoints
SessionAD = Annotated[Session, Depends(get_db_session)]


def check_user_session(db_session: SessionAD, user_session_id) -> bool:
    user_session_id = uuid.UUID(user_session_id) if user_session_id else None
    if user_session_id is None:
        return None
    return web_session.validate(db_session, user_session_id)


def require_valid_user_session(
    db_session: SessionAD,
    user_session_id: Annotated[Union[str, None], Cookie(alias="session")] = None,
) -> bool:
    """
    Check if the session is valid
    """
    valid_user_session = check_user_session(db_session, user_session_id)
    if not valid_user_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No valid session"
        )
    return True


def get_user_session_id(
    user_session_id: Annotated[Union[str, None], Cookie(alias="session")] = None
) -> Optional[str]:
    return user_session_id


def invalidate_user_session(
    db_session: SessionAD, response: Response, user_session_id: str
):
    response.delete_cookie("session")
    web_session.delete(db_session, user_session_id)


def apply_user_session(db_session: SessionAD, response: Response):
    user_session = web_session.create(db_session)
    exp = user_session.created_at.astimezone(datetime.UTC) + SESSION_LIFETIME
    response.set_cookie(
        key="session",
        value=str(user_session.session_id),
        httponly=False,
        samesite="strict",
        expires=exp,
    )


def get_task_controller(connection: HTTPConnection):
    return connection.state.task_controller


TaskControllerAD = Annotated["TaskController", Depends(get_task_controller)]
