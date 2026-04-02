import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List

import sqlalchemy
from sqlalchemy import func, nullslast, or_
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from thymis_controller import db_models, models
from thymis_controller.config import global_settings

logger = logging.getLogger(__name__)


def create_batch(
    session: Session,
    log_entries: list,  # list of models.LogEntry
    ssh_public_key: str,
) -> None:
    if not log_entries:
        return
    # find deployment_info_id by ssh_public_key once for the entire batch
    deployment_info = (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.ssh_public_key == ssh_public_key)
        .first()
    )
    deployment_info_id = deployment_info.id if deployment_info is not None else None

    rows = [
        {
            "id": entry.uuid,
            "timestamp": entry.timestamp,
            "message": entry.message,
            "hostname": entry.host,
            "facility": entry.facility,
            "severity": entry.severity,
            "programname": entry.programname,
            "syslogtag": entry.syslogtag,
            "deployment_info_id": deployment_info_id,
            "ssh_public_key": ssh_public_key,
        }
        for entry in log_entries
    ]

    stmt = sqlite_insert(db_models.LogEntry).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "timestamp": stmt.excluded.timestamp,
            "message": stmt.excluded.message,
            "hostname": stmt.excluded.hostname,
            "facility": stmt.excluded.facility,
            "severity": stmt.excluded.severity,
            "programname": stmt.excluded.programname,
            "syslogtag": stmt.excluded.syslogtag,
            "deployment_info_id": stmt.excluded.deployment_info_id,
            "ssh_public_key": stmt.excluded.ssh_public_key,
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
    max_severity: int | None = None,  # syslog severity (0=Emergency, 3=Error, 7=Debug)
) -> models.LogList:
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
    if max_severity is not None:
        stmt = stmt.filter(db_models.LogEntry.severity <= max_severity)
    stmt = stmt.order_by(nullslast(db_models.LogEntry.timestamp.desc()))
    stmt = stmt.limit(limit).offset(offset)

    results = stmt.all()
    if not results:
        return models.LogList(total_count=0, logs=[])
    total_count = results[0].total_count
    log_entries = [models.LogEntry.from_db_model(row.LogEntry) for row in results]
    return models.LogList(total_count=total_count, logs=log_entries)


def get_log_text(
    session: Session,
    deployment_info: db_models.DeploymentInfo,
    from_datetime: datetime = None,
) -> str:
    stmt = session.query(db_models.LogEntry)
    stmt = stmt.filter(
        or_(
            db_models.LogEntry.deployment_info_id == deployment_info.id,
            db_models.LogEntry.ssh_public_key == deployment_info.ssh_public_key,
        )
    )
    if from_datetime is not None:
        stmt = stmt.filter(db_models.LogEntry.timestamp >= from_datetime)
    stmt = stmt.order_by(nullslast(db_models.LogEntry.timestamp.asc()))

    results = stmt.all()
    log_lines = []
    for log_entry in results:
        timestamp_str = log_entry.timestamp.isoformat().replace("+00:00", "Z")
        log_line = f"{timestamp_str} {log_entry.hostname} {log_entry.syslogtag} {log_entry.message}"
        log_lines.append(log_line)
    return "\n".join(log_lines)


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


def get_program_names(
    session: Session, deployment_info: db_models.DeploymentInfo
) -> List[str]:
    """Get distinct program names for a deployment."""
    program_names = (
        session.query(db_models.LogEntry.programname)
        .filter(
            or_(
                db_models.LogEntry.deployment_info_id == deployment_info.id,
                db_models.LogEntry.ssh_public_key == deployment_info.ssh_public_key,
            )
        )
        .distinct()
        .order_by(db_models.LogEntry.programname)
        .all()
    )
    return [pn[0] for pn in program_names]


def get_latest_log_time(
    session: Session, deployment_info: db_models.DeploymentInfo
) -> datetime:
    """Get the timestamp of the latest log entry for a deployment."""
    latest_log = (
        session.query(db_models.LogEntry)
        .filter(
            or_(
                db_models.LogEntry.deployment_info_id == deployment_info.id,
                db_models.LogEntry.ssh_public_key == deployment_info.ssh_public_key,
            )
        )
        .order_by(db_models.LogEntry.timestamp.desc())
        .first()
    )
    return latest_log.timestamp if latest_log else datetime.now(tz=timezone.utc)
