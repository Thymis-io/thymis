import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from thymis_controller import crud, models
from thymis_controller.dependencies import (
    DBSessionAD,
    NetworkRelayAD,
    ProjectAD,
    require_valid_access_token,
)

router = APIRouter(dependencies=[Depends(require_valid_access_token)])


class StatisticParameters(BaseModel):
    date_from: Optional[datetime.datetime] = None
    date_to: Optional[datetime.datetime] = None

    def get_date_from(self) -> datetime.datetime:
        if self.date_from:
            return self.date_from
        now = datetime.datetime.now()
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def get_date_to(self) -> datetime.datetime:
        if self.date_to:
            return self.date_to
        now = datetime.datetime.now()
        if now.month < 12:
            next_month = now.month + 1
            next_year = now.year
        else:
            next_month = 1
            next_year = now.year + 1
        return datetime.datetime(
            year=next_year,
            month=next_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )


@router.get("/statistics")
def thymis_statistics(
    params: Annotated[StatisticParameters, Depends()],
    db_session: DBSessionAD,
    network_relay: NetworkRelayAD,
    project: ProjectAD,
):
    date_from = params.get_date_from()
    date_to = params.get_date_to()
    current_time = datetime.datetime.now(datetime.timezone.utc)
    currently_connected = [
        models.DeploymentInfo.from_deployment_info(deployment_info_db)
        for deployment_info_db in crud.deployment_info.get_connected_deployment_infos(
            db_session, network_relay
        )
    ]
    max_concurrent_connected = crud.agent_connection.get_max_concurrent_connections(
        db_session, date_from, date_to
    )
    tasks_completed = crud.task.get_tasks_with_state(
        db_session, "completed", date_from, date_to
    )
    tasks_failed = crud.task.get_tasks_with_state(
        db_session, "failed", date_from, date_to
    )
    state = project.read_state()

    return [
        {
            "name": "currently_connected_devices_count",
            "value": len(currently_connected),
            "time": current_time,
        },
        {
            "name": "max_concurrent_connected_devices_count",
            "value": len(max_concurrent_connected),
            "date_from": date_from,
            "date_to": date_to,
        },
        {
            "name": "currently_connected_devices",
            "value": currently_connected,
            "time": current_time,
        },
        {
            "name": "max_concurrent_connected_devices",
            "value": max_concurrent_connected,
            "date_from": date_from,
            "date_to": date_to,
        },
        {
            "name": "tasks_completed_count",
            "value": len(tasks_completed),
            "date_from": date_from,
            "date_to": date_to,
        },
        {
            "name": "tasks_failed_count",
            "value": len(tasks_failed),
            "date_from": date_from,
            "date_to": date_to,
        },
        {
            "name": "project_tags_count",
            "value": len(state.tags),
            "time": current_time,
        },
        {
            "name": "project_configs_count",
            "value": len(state.configs),
            "time": current_time,
        },
    ]
