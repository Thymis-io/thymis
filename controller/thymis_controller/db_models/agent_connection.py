import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from thymis_controller.database.base import Base

if TYPE_CHECKING:
    from thymis_controller.db_models.deployment_info import DeploymentInfo


class AgentConnection(Base):
    __tablename__ = "agent_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    connected_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    disconnected_at: Mapped[datetime] = mapped_column(default=None, nullable=True)

    deployment_info_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deployment_info.id"), nullable=True
    )
    deployment_info: Mapped["DeploymentInfo"] = relationship(lazy=True)
