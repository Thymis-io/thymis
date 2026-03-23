import sqlalchemy.orm
from thymis_controller.db_models.controller_settings import ControllerSettings


def get(db_session: sqlalchemy.orm.Session) -> ControllerSettings:
    settings = db_session.get(ControllerSettings, 1)
    if settings is None:
        settings = ControllerSettings(
            id=1,
            auto_update_enabled=False,
            auto_update_schedule="daily",
        )
        db_session.add(settings)
        db_session.commit()
    return settings


def update(
    db_session: sqlalchemy.orm.Session,
    auto_update_enabled: bool | None = None,
    auto_update_schedule: str | None = None,
) -> ControllerSettings:
    settings = get(db_session)
    if auto_update_enabled is not None:
        settings.auto_update_enabled = auto_update_enabled
    if auto_update_schedule is not None:
        settings.auto_update_schedule = auto_update_schedule
    db_session.commit()
    return settings
