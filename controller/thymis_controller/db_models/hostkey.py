import datetime

from sqlalchemy import Column, DateTime, Integer, String
from thymis_controller.database.base import Base


class HostKey(Base):
    __tablename__ = "hostkeys"

    identifier = Column(String, primary_key=True, index=True)
    build_hash = Column(String)
    public_key = Column(String)
    device_host = Column(String)  # working ip address
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
