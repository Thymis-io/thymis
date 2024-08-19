import os
import pathlib
from urllib.parse import urlparse

from sqlalchemy import create_engine
from thymis_controller.config import global_settings

parsed_url = urlparse(global_settings.DATABASE_URL)
if parsed_url.scheme == "sqlite":
    path = pathlib.Path(parsed_url.path)
    if not path.is_absolute():
        raise ValueError(f"sqlite path must be absolute: {path}")
    if path.is_dir():
        raise ValueError(f"sqlite path must be a file: {path}")
    parent = path.parent
    if not parent.exists():
        os.makedirs(parent)

engine = create_engine(global_settings.DATABASE_URL)
