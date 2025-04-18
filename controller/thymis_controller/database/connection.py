import os
import pathlib
from urllib.parse import urlparse

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from thymis_controller.config import global_settings


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
