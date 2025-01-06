import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from thymis_controller.database.base import Base

if TYPE_CHECKING:
    from thymis_controller.db_models.hardware_device import HardwareDevice


class DeploymentInfo(Base):
    __tablename__ = "deployment_info"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )

    ssh_public_key: Mapped[str] = mapped_column(nullable=False, unique=True)
    deployed_config_commit: Mapped[str]
    deployed_config_id: Mapped[str]

    reachable_deployed_host: Mapped[str | None]

    hardware_devices: Mapped[List["HardwareDevice"]] = relationship(
        back_populates="deployment_info"
    )
