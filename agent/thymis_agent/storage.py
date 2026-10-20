"""Files the agent keeps in its data directory, and how they are written."""

import json
import os
import pathlib
import secrets
from collections.abc import Iterable
from typing import Any, cast

from thymis_agent import logger

DEFAULT_DATA_PATH = pathlib.Path("/etc/thymis")
AGENT_DATA_PATHS = [
    pathlib.Path("/boot/firmware"),  # raspberry-pi-nix generated sd-cards
    pathlib.Path("/boot"),  # boot.loader.efi.efiSysMountPoint
    DEFAULT_DATA_PATH,  # non-nixos systems
]

AGENT_TOKEN_FILENAME = "thymis-token.txt"
AGENT_TOKEN_EXPECTED_FORMAT = (
    "thymis-[0-9a-f]{128}"  # see controller/thymis_controller/task/worker.py `token =`
)
AGENT_METADATA_FILENAME = "thymis-metadata.json"
DEVICE_NONCE_FILENAME = "device-nonce.txt"


def find_file(paths: Iterable[pathlib.Path], *filenames: str) -> pathlib.Path | None:
    """The first of `filenames` that exists, trying each of `paths` in order."""
    for path in paths:
        for filename in filenames:
            file_path = path / filename
            if os.path.exists(file_path):
                return file_path
    return None


def atomic_write(path: str | os.PathLike[str], data: str, mode: int = 0o600) -> None:
    """Durably replace `path` with `data`, forcing its permissions to `mode`.

    rename(2) atomically replaces the destination, so the readable path never
    points at a partial file. fsync of the data before and of the directory
    after means a crash leaves either the old or the new contents, never a
    truncated one.
    """
    path = pathlib.Path(path)
    tmp_path = path.with_name(f"{path.name}.new")
    # create restrictively, then apply `mode`: the content is never readable
    # by anyone else, not even for the instant between create and chmod
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        f = os.fdopen(fd, "w", encoding="utf-8")
    except Exception:
        os.close(fd)
        raise
    with f:
        try:
            # O_CREAT's mode is masked by umask and ignored when tmp_path
            # survived an earlier crash, so set it explicitly
            os.fchmod(f.fileno(), mode)
        except OSError as e:
            # /boot and /boot/firmware are usually vfat, which has no per-file
            # permission bits; the mount's fmask governs instead
            logger.warning("Could not set mode %o on %s: %s", mode, tmp_path, e)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)
    dir_fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def find_data_path() -> pathlib.Path | None:
    """The data directory is the first of `AGENT_DATA_PATHS` holding the token."""
    token_path = find_file(AGENT_DATA_PATHS, AGENT_TOKEN_FILENAME)
    if token_path:
        return token_path.parent
    return None


def find_agent_token() -> str | None:
    token_path = find_file(AGENT_DATA_PATHS, AGENT_TOKEN_FILENAME)
    if token_path:
        with open(token_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def update_token(new_token: str) -> None:
    token_path = find_file(AGENT_DATA_PATHS, AGENT_TOKEN_FILENAME)
    if not token_path:
        token_path = DEFAULT_DATA_PATH / AGENT_TOKEN_FILENAME
        os.makedirs(token_path.parent, exist_ok=True, mode=0o700)
    atomic_write(token_path, new_token)
    logger.info("Token updated successfully")


def get_device_nonce() -> str:
    nonce_path = DEFAULT_DATA_PATH / DEVICE_NONCE_FILENAME
    if nonce_path.exists():
        with open(nonce_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    nonce = secrets.token_hex(32)
    os.makedirs(nonce_path.parent, exist_ok=True, mode=0o700)
    atomic_write(nonce_path, nonce)
    logger.info("Generated new device nonce and stored in %s", nonce_path)
    return nonce


def find_agent_metadata() -> dict[str, Any] | None:
    """The deployed configuration's metadata, with every expected key present."""
    logger.debug("Looking for agent metadata in %s", AGENT_DATA_PATHS)
    metadata_path = find_file(
        AGENT_DATA_PATHS,
        AGENT_METADATA_FILENAME,
        f"{AGENT_METADATA_FILENAME}.old",  # legacy recovery
    )
    if not metadata_path:
        logger.error("Agent metadata not found")
        return None
    logger.debug("Found agent metadata at %s", metadata_path)
    with open(metadata_path, "r", encoding="utf-8") as f:
        val = json.load(f)
    if not isinstance(val, dict):
        logger.error("Agent metadata is not a dict")
        val = {}
    metadata = cast(dict[str, Any], val)
    for key in ["configuration_id", "configuration_commit", "datetime"]:
        metadata.setdefault(key, None)
    return metadata


def update_agent_metadata(metadata: dict[str, Any]) -> None:
    """Persist `metadata`, if the image shipped a metadata file to update."""
    metadata_path = find_file(AGENT_DATA_PATHS, AGENT_METADATA_FILENAME)
    if metadata_path:
        atomic_write(metadata_path, json.dumps(metadata), mode=0o644)
