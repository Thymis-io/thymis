import json

from sqlalchemy import Boolean, Column, Integer, String
from thymis_controller.database.base import Base

DEFAULT_SCHEDULE = json.dumps({"frequency": "daily", "time": "03:00"})


class ControllerSettings(Base):
    __tablename__ = "controller_settings"

    # Single-row table — always id=1
    id = Column(Integer, primary_key=True, default=1)

    auto_update_enabled = Column(Boolean, nullable=False, default=False)
    # JSON-encoded schedule, e.g.:
    #   {"frequency": "daily", "time": "03:00"}
    #   {"frequency": "weekly", "time": "03:00", "weekdays": [0,1,2,3,4]}
    #   {"frequency": "monthly", "time": "03:00", "day_of_month": 1}
    auto_update_schedule = Column(String(512), nullable=False, default=DEFAULT_SCHEDULE)
