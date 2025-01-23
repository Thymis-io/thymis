import uuid

from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column
from thymis_controller.database.base import Base


class AgentToken(Base):
    __tablename__ = "agent_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )

    original_disk_config_commit: Mapped[str] = mapped_column(nullable=False)
    original_disk_config_id: Mapped[str] = mapped_column(nullable=False)
    token: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    revoked: Mapped[bool] = mapped_column(nullable=False, default=False)
