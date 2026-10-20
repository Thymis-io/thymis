import os
import socket

from thymis_agent import logger
from thymis_agent.constants import (
    DEFAULT_DATA_PATH,
    DEVICE_HOSTNAME_FILENAME,
    HOSTNAME_PATH,
)
from thymis_agent.files import atomic_write


def store_hostname(hostname: str | None) -> None:
    path = DEFAULT_DATA_PATH / DEVICE_HOSTNAME_FILENAME
    try:
        if hostname:
            os.makedirs(DEFAULT_DATA_PATH, exist_ok=True, mode=0o700)
            atomic_write(path, hostname + "\n", mode=0o644)
        else:
            path.unlink(missing_ok=True)
    except OSError as e:
        logger.error("Failed to store device hostname: %s", e)


def read_hostname(default_hostname: str) -> str:
    """The stored device hostname, else the deployed default."""
    try:
        device_hostname_path = DEFAULT_DATA_PATH / DEVICE_HOSTNAME_FILENAME
        stored = device_hostname_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        stored = ""
    except OSError as e:
        logger.error("Failed to read device hostname: %s", e)
        stored = ""
    return stored.strip() or default_hostname


def apply_hostname(hostname: str) -> bool:
    """Set `hostname`. Returns True if the hostname changed."""
    try:
        return _set_hostname(hostname)
    except OSError as e:
        logger.error("Failed to apply hostname %r: %s", hostname, e)
        return False


def _set_hostname(hostname: str) -> bool:
    changed = False
    try:
        static_hostname = HOSTNAME_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        static_hostname = None
    if static_hostname != hostname:
        atomic_write(HOSTNAME_PATH, hostname + "\n", mode=0o644)
        changed = True
    if socket.gethostname() != hostname:
        socket.sethostname(hostname)
        changed = True
    if changed:
        logger.info("Hostname set to: %s", hostname)
    return changed
