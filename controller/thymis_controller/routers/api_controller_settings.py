import json
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from thymis_controller import crud
from thymis_controller.dependencies import DBSessionAD

router = APIRouter()


class AutoUpdateSchedule(BaseModel):
    frequency: Literal["daily", "weekly", "monthly", "monthly_weekday"] = "daily"
    time: str = "03:00"  # HH:MM, used for daily/weekly/monthly
    weekdays: Optional[List[int]] = [0, 1, 2, 3]  # 0=Mon … 6=Sun, for daily (multi)
    weekday: Optional[
        int
    ] = None  # 0=Mon … 6=Sun, for weekly (single) and monthly_weekday
    day_of_month: Optional[int] = None  # 1–28, for monthly
    nth_weekday: Optional[int] = None  # 1–5 or -1 (last), for monthly_weekday


class ControllerSettingsResponse(BaseModel):
    auto_update_enabled: bool
    auto_update_schedule: AutoUpdateSchedule


class ControllerSettingsPatch(BaseModel):
    auto_update_enabled: Optional[bool] = None
    auto_update_schedule: Optional[AutoUpdateSchedule] = None


def _parse_schedule(raw: str) -> AutoUpdateSchedule:
    try:
        data = json.loads(raw)
        return AutoUpdateSchedule(**data)
    except Exception:
        return AutoUpdateSchedule()


@router.get("/controller-settings", response_model=ControllerSettingsResponse)
def get_controller_settings(db_session: DBSessionAD):
    settings = crud.controller_settings.get(db_session)
    return ControllerSettingsResponse(
        auto_update_enabled=settings.auto_update_enabled,
        auto_update_schedule=_parse_schedule(settings.auto_update_schedule),
    )


@router.patch("/controller-settings", response_model=ControllerSettingsResponse)
def patch_controller_settings(body: ControllerSettingsPatch, db_session: DBSessionAD):
    schedule_raw = None
    if body.auto_update_schedule is not None:
        if (
            body.auto_update_schedule.frequency == "daily"
            and not body.auto_update_schedule.weekdays
        ):
            raise HTTPException(
                status_code=422, detail="weekdays required for daily frequency"
            )
        if (
            body.auto_update_schedule.frequency == "weekly"
            and body.auto_update_schedule.weekday is None
        ):
            raise HTTPException(
                status_code=422, detail="weekday required for weekly frequency"
            )
        if (
            body.auto_update_schedule.frequency == "monthly"
            and body.auto_update_schedule.day_of_month is None
        ):
            raise HTTPException(
                status_code=422, detail="day_of_month required for monthly frequency"
            )
        if body.auto_update_schedule.frequency == "monthly_weekday" and (
            body.auto_update_schedule.nth_weekday is None
            or body.auto_update_schedule.weekday is None
        ):
            raise HTTPException(
                status_code=422,
                detail="nth_weekday and weekday required for monthly_weekday frequency",
            )
        schedule_raw = body.auto_update_schedule.model_dump_json(exclude_none=True)

    settings = crud.controller_settings.update(
        db_session,
        auto_update_enabled=body.auto_update_enabled,
        auto_update_schedule=schedule_raw,
    )
    return ControllerSettingsResponse(
        auto_update_enabled=settings.auto_update_enabled,
        auto_update_schedule=_parse_schedule(settings.auto_update_schedule),
    )
