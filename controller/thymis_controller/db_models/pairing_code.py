import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from thymis_controller.database.base import Base

if TYPE_CHECKING:
    from thymis_controller.db_models.agent_token import AgentToken


class PairingCode(Base):
    """A short, human-typeable alias for an agent token that already exists."""

    __tablename__ = "pairing_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(nullable=False)
    normalized_code: Mapped[str] = mapped_column(
        nullable=False, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked: Mapped[bool] = mapped_column(nullable=False, default=False)
    redeemed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    successor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_tokens.id"),
        nullable=False,
        index=True,
    )

    successor: Mapped["AgentToken"] = relationship()
