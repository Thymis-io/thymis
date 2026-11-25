import asyncio
import logging
import os
import pathlib
from urllib.parse import urlparse

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
    # The hourly retention delete can hold the write lock for a while on a
    # multi-GB log table. Waiting is much better than failing a log batch.
    engine = create_engine(
        get_db_url(),
        pool_size=20,
        max_overflow=40,
        connect_args={"timeout": 60},
    )
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
