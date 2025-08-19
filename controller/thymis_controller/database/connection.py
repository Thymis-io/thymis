import asyncio
import logging
import os
import pathlib
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
    cursor.close()


def enable_auto_vacuum(db_session: Session):
    auto_vacuum = db_session.execute(sqlalchemy.text("PRAGMA auto_vacuum")).scalar()
    if auto_vacuum == 0:
        db_session.execute(sqlalchemy.text("PRAGMA auto_vacuum = 1"))
        db_session.commit()
        logger.info("Enabled auto_vacuum for the database")


def compact_database(db_session: Session):
    logger.info("Running VACUUM to compact the database...")
    db_session.execute(sqlalchemy.text("VACUUM"))
    db_session.execute(sqlalchemy.text("PRAGMA wal_checkpoint(TRUNCATE)"))
    db_session.commit()
    logger.info("Vacuum and WAL checkpoint completed")


async def initialize_cleanup(db_engine: Engine):
    with Session(db_engine) as session:
        enable_auto_vacuum(session)
        await crud.logs.remove_expired_logs(session)
        compact_database(session)
    # Also do initial image cleanup
    await images.periodic_image_cleanup()


async def periodic_cleanup_loop(db_engine: Engine):
    await initialize_cleanup(db_engine)

    while True:
        await asyncio.sleep(global_settings.LOG_CLEANUP_INTERVAL_SECONDS)
        with Session(db_engine) as session:
            await crud.logs.remove_expired_logs(session)
        # Clean up old images periodically
        await images.periodic_image_cleanup()
