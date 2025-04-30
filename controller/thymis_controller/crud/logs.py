import uuid
from datetime import datetime

from sqlalchemy import nullslast
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
