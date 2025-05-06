import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from thymis_controller import crud
from thymis_controller.dependencies import DBSessionAD, NetworkRelayAD

router = APIRouter()


class MetricParameters(BaseModel):
    range_from: Optional[datetime.datetime] = None
    range_to: Optional[datetime.datetime] = None

    def get_range_from(self) -> datetime.datetime:
        if self.range_from:
            return self.range_from
        now = datetime.datetime.now()
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def get_range_to(self) -> datetime.datetime:
        if self.range_to:
            return self.range_to
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


@router.get("/thymis/metrics", tags=["metrics"])
def metrics(
    params: Annotated[MetricParameters, Query()],
    db_session: DBSessionAD,
    network_relay: NetworkRelayAD,
):
    currently_connected = crud.deployment_info.get_connected_deployment_infos(
        db_session, network_relay
    )
    max_concurrent_connected = crud.agent_connection.get_max_concurrent_connections(
        db_session,
        params.get_range_from(),
        params.get_range_to(),
    )

    return {
        "range_from": params.get_range_from(),
        "range_to": params.get_range_to(),
        "metrics": [
            {
                "name": "currently_connected_devices_count",
                "value": len(currently_connected),
            },
            {
                "name": "max_concurrent_connected_devices_count",
                "value": len(max_concurrent_connected),
            },
            {
                "name": "currently_connected_devices",
                "value": currently_connected,
            },
            {
                "name": "max_concurrent_connected_devices",
                "value": max_concurrent_connected,
            },
        ],
    }
