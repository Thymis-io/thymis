import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from thymis_controller.database.base import Base

if TYPE_CHECKING:
    from thymis_controller.db_models.deployment_info import DeploymentInfo


class HardwareDevice(Base):
    __tablename__ = "hardware_devices"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True
    )

    hardware_id: Mapped[str]

    deployment_info_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deployment_info.id")
    )
    deployment_info: Mapped["DeploymentInfo"] = relationship(
        back_populates="hardware_devices"
    )