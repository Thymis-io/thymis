import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Integer, LargeBinary, Text
from sqlalchemy.dialects.postgresql import UUID
from thymis_controller.database.base import Base


class SecretTypes(enum.Enum):
    SINGLE_LINE = "single_line"
    MULTI_LINE = "multi_line"
    ENV_LIST = "env_list"
    FILE = "file"


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(Text, nullable=False)
    type = Column(Enum(SecretTypes), nullable=False)
    value_enc = Column(LargeBinary, nullable=False)
    value_size = Column(Integer, nullable=False)  # bytes
    filename = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    delete_at = Column(DateTime(timezone=True), nullable=True)
