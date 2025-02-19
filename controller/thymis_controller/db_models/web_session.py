from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from thymis_controller.database.base import Base


class WebSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<Session {self.session_id}>"
