import datetime
import logging
import uuid
from typing import Annotated, Generator, Optional, Union

from fastapi import Cookie, Depends, HTTPException, Request, Response, WebSocket, status
from fastapi.requests import HTTPConnection
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from thymis_controller.config import global_settings
from thymis_controller.crud import web_session
from thymis_controller.network_relay import NetworkRelay
from thymis_controller.notifications import NotificationManager
from thymis_controller.project import Project
from thymis_controller.task.controller import TaskController

logger = logging.getLogger(__name__)


def get_project(connection: HTTPConnection) -> Project:
    return connection.state.project


ProjectAD = Annotated[Project, Depends(get_project)]


def get_network_relay(connection: HTTPConnection) -> NetworkRelay:
    return connection.state.network_relay


NetworkRelayAD = Annotated[NetworkRelay, Depends(get_network_relay)]


def get_state(project: Project = Depends(get_project)):
    return project.read_state()


def get_db_engine(connection: HTTPConnection):
    return connection.state.engine


EngineAD = Annotated[Engine, Depends(get_db_engine)]


def get_db_session(connection: HTTPConnection) -> Generator[Session, None, None]:
    start_connection_time = datetime.datetime.now()
    with Session(connection.state.engine) as session:
        yield session
    connection_time = datetime.datetime.now() - start_connection_time
    if connection_time > datetime.timedelta(seconds=1):
        logger.warning(
            f"Database connection lifetime: {connection_time.total_seconds()}s for {connection.scope['path']}"
        )


# session annotated dependency for FastAPI endpoints
SessionAD = Annotated[Session, Depends(get_db_session)]

UserSessionIDAD = Annotated[Union[uuid.UUID, None], Cookie(alias="session-id")]

UserSessionTokenAD = Annotated[Union[str, None], Cookie(alias="session-token")]


def check_user_session(
    db_session: SessionAD, user_session_id: uuid.UUID, user_session_token: str
) -> Optional[bool]:
    if user_session_id is None or user_session_token is None:
        return None
    return web_session.validate(db_session, user_session_id, user_session_token)


def require_valid_user_session(
    db_engine: EngineAD,
    user_session_id: UserSessionIDAD,
    user_session_token: UserSessionTokenAD,
) -> bool:
    """
    Check if the session is valid
    """
    with Session(db_engine) as db_session:
        valid_user_session = check_user_session(
            db_session, user_session_id, user_session_token
        )
    if not valid_user_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No valid session"
        )
    return True


def get_user_session_token(
    user_session_token: Annotated[
        Union[uuid.UUID, None], Cookie(alias="session-token")
    ] = None
) -> Optional[str]:
    return user_session_token


def invalidate_user_session(
    db_session: SessionAD,
    response: Response,
    user_session_id: uuid.UUID,
    user_session_token: str,
):
    if not web_session.validate(db_session, user_session_id, user_session_token):
        return
    response.delete_cookie("session-id")
    response.delete_cookie("session-token")
    web_session.delete(db_session, user_session_id)


def apply_user_session(db_session: SessionAD, response: Response):
    user_session = web_session.create(db_session)
    exp = (
        user_session.created_at.astimezone(datetime.UTC) + web_session.SESSION_LIFETIME
    )
    is_using_https = global_settings.BASE_URL.startswith("https")
    response.set_cookie(
        key="session-id",
        value=str(user_session.id),
        httponly=True,
        secure=is_using_https,
        samesite="strict",
        expires=exp,
    )
    response.set_cookie(
        key="session-token",
        value=user_session.session_token,
        httponly=True,
        secure=is_using_https,
        samesite="strict",
        expires=exp,
    )


def get_task_controller(connection: HTTPConnection) -> "TaskController":
    return connection.state.task_controller


TaskControllerAD = Annotated["TaskController", Depends(get_task_controller)]


def get_notification_manager(connection: HTTPConnection) -> "NotificationManager":
    return connection.state.notification_manager


NotificationManagerAD = Annotated[
    "NotificationManager", Depends(get_notification_manager)
]
