import asyncio
import logging
import uuid
from datetime import datetime, timedelta

import sqlalchemy
from sqlalchemy import func, nullslast, or_
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from thymis_controller import db_models
from thymis_controller.config import global_settings

logger = logging.getLogger(__name__)


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
    program_name: str = None,
    exact_program_name: bool = False,
    limit: int = 100,
    offset: int = 0,
):
    # where ID equals or ssh public key equals

    stmt = session.query(db_models.LogEntry, func.count().over().label("total_count"))
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
    if program_name is not None:
        if exact_program_name:
            stmt = stmt.filter(db_models.LogEntry.programname == program_name)
        else:
            stmt = stmt.filter(db_models.LogEntry.programname.contains(program_name))
    stmt = stmt.order_by(nullslast(db_models.LogEntry.timestamp.desc()))
    stmt = stmt.limit(limit).offset(offset)

    results = stmt.all()
    if not results:
        return [], 0
    total_count = results[0].total_count
    log_entries = [row.LogEntry for row in results]
    return log_entries, total_count


def delete_expired_log_batch(
    session: Session, cutoff_date: datetime, limit: int
) -> int:
    result = session.execute(
        sqlalchemy.text(
            """
            DELETE FROM log_entries
            WHERE rowid IN (
                SELECT rowid FROM log_entries
                WHERE timestamp < :cutoff
                LIMIT :limit
            );
            """
        ),
        {"cutoff": cutoff_date, "limit": limit},
    )
    session.commit()
    return result.rowcount


async def remove_expired_logs(session: Session) -> int:
    cutoff_date = datetime.now() - timedelta(days=global_settings.LOG_RETENTION_DAYS)
    batch_count = 10_000
    delete_count = (
        session.query(db_models.LogEntry)
        .filter(db_models.LogEntry.timestamp < cutoff_date)
        .count()
    )
    if delete_count == 0:
        return 0
    logger.info(
        "Removing %d logs older than %d days, cutoff date: %s...",
        delete_count,
        global_settings.LOG_RETENTION_DAYS,
        cutoff_date,
    )
    total_deleted = 0
    while True:
        await asyncio.sleep(0.1)  # avoid blocking the database and event loop
        deleted = delete_expired_log_batch(session, cutoff_date, limit=batch_count)
        total_deleted += deleted
        if deleted == 0:
            break
        if total_deleted % (batch_count * 10) == 0:
            logger.info(
                "Deleted %d/%d expired log entries", total_deleted, delete_count
            )
    logger.info("Deleted a total of %d expired log entries", total_deleted)
