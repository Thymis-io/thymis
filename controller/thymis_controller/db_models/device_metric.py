import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from thymis_controller.database.base import Base

if TYPE_CHECKING:
    from thymis_controller.db_models.deployment_info import DeploymentInfo


class DeviceMetric(Base):
    __tablename__ = "device_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    deployment_info_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deployment_info.id"), nullable=False
    )
    deployment_info: Mapped["DeploymentInfo"] = relationship(lazy=True)
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    cpu_percent: Mapped[float] = mapped_column(nullable=False)
    ram_percent: Mapped[float] = mapped_column(nullable=False)
    disk_percent: Mapped[float] = mapped_column(nullable=False)

    __table_args__ = (
        Index(
            "ix_device_metrics_deployment_timestamp",
            "deployment_info_id",
            "timestamp",
        ),
    )
