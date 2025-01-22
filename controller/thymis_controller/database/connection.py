import os
import pathlib
from urllib.parse import urlparse

from sqlalchemy import create_engine
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
    return create_engine(get_db_url())
