import asyncio
import logging
import os
import pathlib
import time
from urllib.parse import urlparse

import sqlalchemy
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from thymis_controller import crud
from thymis_controller.config import global_settings
from thymis_controller.crud import images

logger = logging.getLogger(__name__)


def get_db_url():
    return str(
        f"sqlite:///{str((global_settings.PROJECT_PATH / 'thymis.sqlite').resolve())}"
    )


def create_sqlalchemy_engine():
    parsed_url = urlparse(get_db_url())
    if parsed_url.scheme == "sqlite":
        path = pathlib.Path(parsed_url.path)
        if not path.is_absolute():
            raise ValueError(f"sqlite path must be absolute: {path}")
        if path.is_dir():
            raise ValueError(f"sqlite path must be a file: {path}")
        parent = path.parent
        if not parent.exists():
            os.makedirs(parent)
    engine = create_engine(get_db_url(), pool_size=20, max_overflow=40)
    return engine


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=normal")
    cursor.execute("PRAGMA cache_size = -2000")
    # FILE, not MEMORY: large sorts and VACUUM would otherwise grow anonymous
    # memory in proportion to the database size (a 3 GB log table pushed the
    # controller into its cgroup's MemoryHigh).
    cursor.execute("PRAGMA temp_store = FILE")
    cursor.close()


def enable_auto_vacuum(db_session: Session) -> bool:
    """Turn on auto_vacuum, returning True when a VACUUM is required to apply it."""
    auto_vacuum = db_session.execute(sqlalchemy.text("PRAGMA auto_vacuum")).scalar()
    if auto_vacuum == 0:
        db_session.execute(sqlalchemy.text("PRAGMA auto_vacuum = 1"))
        db_session.commit()
        logger.info("Enabled auto_vacuum for the database")
        return True
    return False


def compact_database(db_engine: Engine):
    logger.info("Running VACUUM to compact the database...")
    start_time = time.monotonic()
    with Session(db_engine) as db_session:
        db_session.execute(sqlalchemy.text("VACUUM"))
        db_session.execute(sqlalchemy.text("PRAGMA wal_checkpoint(TRUNCATE)"))
        db_session.commit()
    logger.info(
        "Vacuum and WAL checkpoint completed in %.2fs", time.monotonic() - start_time
    )


def _delete_expired_metrics(session: Session) -> None:
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(
        days=global_settings.METRICS_RETENTION_DAYS
    )
    deleted = crud.device_metric.delete_expired_metrics(session, cutoff)
    if deleted:
        logger.info("Deleted %d expired device metrics", deleted)


async def initialize_cleanup(db_engine: Engine):
    with Session(db_engine) as session:
        # Only VACUUM when auto_vacuum was just enabled and the database is
        # still fresh. Running it on every start rewrote the whole multi-GB log
        # table while holding the write lock, which stalled ingest long enough
        # for every device's rsyslog omhttp action to time out and retry; with
        # temp_store=MEMORY it also left multi-GB anonymous mappings behind.
        if await asyncio.to_thread(enable_auto_vacuum, session):
            await asyncio.to_thread(compact_database, db_engine)
        await crud.logs.remove_expired_logs(session)
        await asyncio.to_thread(_delete_expired_metrics, session)
    # Also do initial image cleanup
    await images.periodic_image_cleanup()


async def periodic_cleanup_loop(db_engine: Engine):
    await initialize_cleanup(db_engine)

    while True:
        await asyncio.sleep(global_settings.LOG_CLEANUP_INTERVAL_SECONDS)
        with Session(db_engine) as session:
            await crud.logs.remove_expired_logs(session)
            await asyncio.to_thread(_delete_expired_metrics, session)
        # Clean up old images periodically
        await images.periodic_image_cleanup()
