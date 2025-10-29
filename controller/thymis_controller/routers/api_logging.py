import datetime
import uuid

from fastapi import APIRouter, Response
from thymis_controller import db_models
from thymis_controller.crud.logs import get_logs
from thymis_controller.dependencies import DBSessionAD

router = APIRouter()


@router.get("/logs/{deployment_info_id}")
def get_tasks(
    session: DBSessionAD,
    deployment_info_id: uuid.UUID,
    from_datetime: str = None,
    to_datetime: str = None,
    program_name: str = None,
    exact_program_name: bool = False,
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

    logs, total_count = get_logs(
        session,
        deployment_info=deployment_info,
        from_datetime=(
            datetime.datetime.fromisoformat(from_datetime) if from_datetime else None
        ),
        to_datetime=(
            datetime.datetime.fromisoformat(to_datetime) if to_datetime else None
        ),
        program_name=program_name,
        exact_program_name=exact_program_name,
        limit=limit,
        offset=offset,
    )
    return {
        "total_count": total_count,
        "logs": logs,
    }


@router.get("/logs/{deployment_info_id}/program-names")
def get_log_program_names(
    session: DBSessionAD,
    deployment_info_id: uuid.UUID,
):
    deployment_info = (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.id == deployment_info_id)
        .first()
    )
    if deployment_info is None:
        return Response(status_code=404)

    program_names = (
        session.query(db_models.LogEntry.programname)
        .filter(
            db_models.LogEntry.deployment_info_id == deployment_info.id,
        )
        .distinct()
        .order_by(db_models.LogEntry.programname)
        .all()
    )
    return [pn[0] for pn in program_names]
