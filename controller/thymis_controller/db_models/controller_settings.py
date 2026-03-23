from sqlalchemy import Boolean, Column, Integer, String
from thymis_controller.database.base import Base


class ControllerSettings(Base):
    __tablename__ = "controller_settings"

    # Single-row table — always id=1
    id = Column(Integer, primary_key=True, default=1)

    auto_update_enabled = Column(Boolean, nullable=False, default=False)
    # systemd OnCalendar expression, e.g. "daily" or "*-*-* 03:00:00"
    auto_update_schedule = Column(String(255), nullable=False, default="daily")
