import datetime
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from thymis_controller import crud, models
from thymis_controller.crud.logs import (
    get_latest_log_time,
    get_log_text,
    get_logs,
    get_program_names,
)
from thymis_controller.dependencies import DBSessionAD

router = APIRouter()


@router.get("/logs/{deployment_info_id}", response_model=models.LogList)
def get_logs_endpoint(
    session: DBSessionAD,
    deployment_info_id: uuid.UUID,
    from_datetime: str = None,
    to_datetime: str = None,
    program_name: str = None,
    exact_program_name: bool = False,
    limit: int = 100,
    offset: int = 0,
):
    deployment_info = crud.deployment_info.get_by_id(session, deployment_info_id)
    if deployment_info is None:
        raise HTTPException(status_code=404, detail="Deployment not found")

    log_list = get_logs(
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
    return log_list


@router.get("/logs/{deployment_info_id}/program-names")
def get_log_program_names(
    session: DBSessionAD,
    deployment_info_id: uuid.UUID,
):
    deployment_info = crud.deployment_info.get_by_id(session, deployment_info_id)
    if deployment_info is None:
        raise HTTPException(status_code=404, detail="Deployment not found")

    return get_program_names(session, deployment_info)


@router.get("/logs/{deployment_info_id}/download", response_class=PlainTextResponse)
def download_logs(
    session: DBSessionAD, deployment_info_id: uuid.UUID, duration_minutes: int
):
    deployment_info = crud.deployment_info.get_by_id(session, deployment_info_id)
    if deployment_info is None:
        raise HTTPException(status_code=404, detail="Deployment not found")

    latest_log_time = get_latest_log_time(session, deployment_info)
    from_datetime = latest_log_time - datetime.timedelta(minutes=duration_minutes)

    content = get_log_text(session, deployment_info, from_datetime)

    return PlainTextResponse(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="logs_{deployment_info.deployed_config_id}_{from_datetime.isoformat()}.txt"'
        },
    )
