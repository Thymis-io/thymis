import uuid
from datetime import datetime

from sqlalchemy import nullslast
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from thymis_controller import db_models

# class LogEntry(Base):
#     __tablename__ = "log_entries"

#     id: Mapped[uuid.UUID] = mapped_column(
#         Uuid(as_uuid=True), primary_key=True, index=True
#     )
#     timestamp: Mapped[datetime] = mapped_column(
#         nullable=False
#     )
#     message: Mapped[str] = mapped_column(nullable=False)
#     hostname: Mapped[str] = mapped_column(nullable=False)
#     facility: Mapped[int] = mapped_column(nullable=False)
#     severity: Mapped[int] = mapped_column(nullable=False)
#     programname: Mapped[str] = mapped_column(nullable=False)
#     syslogtag: Mapped[str] = mapped_column(nullable=False)

#     deployment_info_id: Mapped[Optional[uuid.UUID]] = mapped_column(
#         ForeignKey("deployment_info.id"), nullable=True
#     )
#     ssh_public_key: Mapped[str] = mapped_column(nullable=False) # used if no deployment_info_id available


def create(
    session: Session,
    id: uuid.UUID,
    timestamp: datetime,
    message: str,
    hostname: str,
    facility: int,
    severity: int,
    programname: str,
    syslogtag: str,
    ssh_public_key: str,
):
    # find deployment_info_id by ssh_public_key, if not exists, just write without it
    deployment_info = (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.ssh_public_key == ssh_public_key)
        .first()
    )
    if deployment_info is not None:
        deployment_info_id = deployment_info.id
    else:
        deployment_info_id = None
    # new_log_entry = db_models.LogEntry(
    #     id=id,
    #     timestamp=timestamp,
    #     message=message,
    #     hostname=hostname,
    #     facility=facility,
    #     severity=severity,
    #     programname=programname,
    #     syslogtag=syslogtag,
    #     deployment_info_id=deployment_info_id,
    #     ssh_public_key=ssh_public_key,
    # )
    # session.add(new_log_entry)
    stmt = sqlite_insert(db_models.LogEntry).values(
        [
            {
                "id": id,
                "timestamp": timestamp,
                "message": message,
                "hostname": hostname,
                "facility": facility,
                "severity": severity,
                "programname": programname,
                "syslogtag": syslogtag,
                "deployment_info_id": deployment_info_id,
                "ssh_public_key": ssh_public_key,
            }
        ]
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "timestamp": timestamp,
            "message": message,
            "hostname": hostname,
            "facility": facility,
            "severity": severity,
            "programname": programname,
            "syslogtag": syslogtag,
            "deployment_info_id": deployment_info_id,
            "ssh_public_key": ssh_public_key,
        },
    )
    session.execute(stmt)
    session.commit()
