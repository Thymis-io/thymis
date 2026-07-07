import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import sqlalchemy
from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from thymis_controller.database.base import Base

if TYPE_CHECKING:
    from thymis_controller.db_models.agent_token import AccessClientToken
    from thymis_controller.db_models.hardware_device import HardwareDevice


class LogEntry(Base):
    __tablename__ = "log_entries"
    __table_args__ = (
        # Composite indexes for the common query pattern:
        # filter by deployment_info_id/ssh_public_key + order by timestamp DESC
        sqlalchemy.Index(
            "ix_log_entries_deployment_info_id_timestamp",
            "deployment_info_id",
            "timestamp",
        ),
        sqlalchemy.Index(
            "ix_log_entries_ssh_public_key_timestamp", "ssh_public_key", "timestamp"
        ),
        sqlalchemy.Index(
            "ix_log_entries_deployment_info_id_programname",
            "deployment_info_id",
            "programname",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    message: Mapped[str] = mapped_column(nullable=False)
    hostname: Mapped[str] = mapped_column(nullable=False)
    facility: Mapped[int] = mapped_column(nullable=False)
    severity: Mapped[int] = mapped_column(nullable=False)
    programname: Mapped[str] = mapped_column(nullable=False)
    syslogtag: Mapped[str] = mapped_column(nullable=False)

    deployment_info_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("deployment_info.id"), nullable=True
    )
    ssh_public_key: Mapped[str] = mapped_column(
        nullable=False
    )  # used if no deployment_info_id available
