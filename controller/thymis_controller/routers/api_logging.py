import datetime
import uuid

from fastapi import APIRouter, Response, WebSocket
from thymis_controller import db_models
from thymis_controller.crud.logs import get_logs
from thymis_controller.dependencies import (
    DBSessionAD,
    EngineAD,
    NetworkRelayAD,
    ProjectAD,
    TaskControllerAD,
)
from thymis_controller.routers.frontend import is_running_in_playwright
from thymis_controller.task.subscribe_ui import TaskWebsocketSubscriber

router = APIRouter()


@router.get("/logs/{deployment_info_id}")
def get_tasks(
    session: DBSessionAD,
    deployment_info_id: uuid.UUID,
    from_datetime: str = None,
    to_datetime: str = None,
    limit: int = 100,
    offset: int = 0,
):
    deployment_info = (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.id == deployment_info_id)
        .first()
    )
    if deployment_info is None:
        return Response(status_code=404)

    logs = get_logs(
        session,
        deployment_info=deployment_info,
        from_datetime=datetime.datetime.fromisoformat(from_datetime),
        to_datetime=datetime.datetime.fromisoformat(to_datetime),
        limit=limit,
        offset=offset,
    )
    return logs
