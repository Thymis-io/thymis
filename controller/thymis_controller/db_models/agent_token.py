import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from thymis_controller.database.base import Base

if TYPE_CHECKING:
    from thymis_controller.db_models.deployment_info import DeploymentInfo
    from thymis_controller.db_models.pairing_code import PairingCode
    from thymis_controller.db_models.task import Task


class AgentToken(Base):
    __tablename__ = "agent_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    original_disk_config_commit: Mapped[str | None] = mapped_column(nullable=True)
    original_disk_config_id: Mapped[str | None] = mapped_column(nullable=True)
    token: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    revoked: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Null for image-baked tokens, which have no code.
    pairing_code_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("pairing_codes.id"),
        nullable=True,
        unique=True,
        index=True,
    )

    pairing_code: Mapped["PairingCode | None"] = relationship(
        back_populates="successor"
    )


class AccessClientToken(Base):
    __tablename__ = "access_client_tokens"

    token: Mapped[str] = mapped_column(
        primary_key=True, nullable=False, unique=True, index=True
    )
    revoked: Mapped[bool] = mapped_column(nullable=False, default=False)

    for_deployment_info_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("deployment_info.id"),
        nullable=False,
        index=True,
    )

    for_deployment_info: Mapped["DeploymentInfo"] = relationship(
        back_populates="access_client_tokens"
    )

    deploy_device_task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id"), nullable=True, index=True
    )

    deploy_device_task: Mapped["Task"] = relationship(
        back_populates="access_client_tokens"
    )
