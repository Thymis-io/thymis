import uuid
from datetime import datetime

from sqlalchemy import nullslast, or_
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from thymis_controller import db_models


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


def get_logs(
    session: Session,
    deployment_info: db_models.DeploymentInfo,
    from_datetime: datetime = None,
    to_datetime: datetime = None,
    limit: int = 100,
    offset: int = 0,
):
    # where ID equals or ssh public key equals

    stmt = session.query(db_models.LogEntry)
    stmt = stmt.filter(
        or_(
            db_models.LogEntry.deployment_info_id == deployment_info.id,
            db_models.LogEntry.ssh_public_key == deployment_info.ssh_public_key,
        )
    )
    if from_datetime is not None:
        stmt = stmt.filter(db_models.LogEntry.timestamp >= from_datetime)
    if to_datetime is not None:
        stmt = stmt.filter(db_models.LogEntry.timestamp <= to_datetime)
    stmt = stmt.order_by(nullslast(db_models.LogEntry.timestamp.desc()))
    stmt = stmt.limit(limit).offset(offset)
    return stmt.all()
