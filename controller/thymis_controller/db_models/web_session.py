from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Uuid
from thymis_controller.database.base import Base


class WebSession(Base):
    __tablename__ = "sessions"

    id = Column(Uuid, primary_key=True, index=True)
    session_token = Column(String, unique=True, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    username = Column(String, nullable=True)
    given_name = Column(String, nullable=True)
    family_name = Column(String, nullable=True)
    email = Column(String, nullable=True)

    def __repr__(self):
        return f"<Session {self.id}>"
