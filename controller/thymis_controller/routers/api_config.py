import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from thymis_controller import crud
from typing_extensions import Literal

logger = logging.getLogger(__name__)

router = APIRouter(tags=["config"])


@router.get("/config/check-systemd-timer")
def check_systemd_timer_config(
    timer_type: Literal["calendar", "timespan"],
    value: str,
    iterations: Optional[int] = 1,
):
    if timer_type == "calendar":
        try:
            return crud.check_systemd_timer.check_calendar(value, iterations)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    elif timer_type == "timespan":
        try:
            return crud.check_systemd_timer.check_timespan(value)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    else:
        raise HTTPException(status_code=400, detail="Invalid timer type")
