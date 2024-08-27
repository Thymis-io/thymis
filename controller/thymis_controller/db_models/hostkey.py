import datetime

from sqlalchemy import Column, DateTime, Integer, String
from thymis_controller.database.base import Base


class HostKey(Base):
    __tablename__ = "hostkeys"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    build_hash = Column(String, unique=True)
    public_key = Column(String)
    identifier = Column(String, unique=True)
    device_host = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
