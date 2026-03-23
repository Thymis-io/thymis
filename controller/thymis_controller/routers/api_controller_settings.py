from fastapi import APIRouter
from pydantic import BaseModel
from thymis_controller import crud
from thymis_controller.dependencies import DBSessionAD

router = APIRouter()


class ControllerSettingsResponse(BaseModel):
    auto_update_enabled: bool
    auto_update_schedule: str


class ControllerSettingsPatch(BaseModel):
    auto_update_enabled: bool | None = None
    auto_update_schedule: str | None = None


@router.get("/controller-settings", response_model=ControllerSettingsResponse)
def get_controller_settings(db_session: DBSessionAD):
    settings = crud.controller_settings.get(db_session)
    return ControllerSettingsResponse(
        auto_update_enabled=settings.auto_update_enabled,
        auto_update_schedule=settings.auto_update_schedule,
    )


@router.patch("/controller-settings", response_model=ControllerSettingsResponse)
def patch_controller_settings(body: ControllerSettingsPatch, db_session: DBSessionAD):
    settings = crud.controller_settings.update(
        db_session,
        auto_update_enabled=body.auto_update_enabled,
        auto_update_schedule=body.auto_update_schedule,
    )
    return ControllerSettingsResponse(
        auto_update_enabled=settings.auto_update_enabled,
        auto_update_schedule=settings.auto_update_schedule,
    )
