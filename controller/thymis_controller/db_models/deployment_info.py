import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from thymis_controller.database.base import Base

if TYPE_CHECKING:
    from thymis_controller.db_models.agent_token import AccessClientToken
    from thymis_controller.db_models.hardware_device import HardwareDevice


class DeploymentInfo(Base):
    __tablename__ = "deployment_info"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )

    ssh_public_key: Mapped[str] = mapped_column(nullable=False)
    deployed_config_commit: Mapped[str | None] = mapped_column(nullable=True)
    deployed_config_id: Mapped[str | None] = mapped_column(nullable=True)

    reachable_deployed_host: Mapped[str | None]

    hardware_devices: Mapped[List["HardwareDevice"]] = relationship(
        back_populates="deployment_info"
    )

    access_client_tokens: Mapped[List["AccessClientToken"]] = relationship(
        back_populates="for_deployment_info"
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "ssh_public_key": self.ssh_public_key,
            "deployed_config_commit": self.deployed_config_commit,
            "deployed_config_id": self.deployed_config_id,
            "reachable_deployed_host": self.reachable_deployed_host,
        }
