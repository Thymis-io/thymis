import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from thymis_controller.database.base import Base


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    identifier = Column(String)
    build_hash = Column(String)
    commit_hash = Column(String)
    device_state = Column(JSON)
    valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
