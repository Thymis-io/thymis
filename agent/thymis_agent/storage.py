import json
import os
import secrets

from thymis_agent import logger
from thymis_agent.constants import (
    AGENT_DATA_PATHS,
    AGENT_METADATA_FILENAME,
    AGENT_TOKEN_FILENAME,
    DEFAULT_DATA_PATH,
)
from thymis_agent.files import atomic_write, find_file, find_file_multiple_names


def find_agent_token():
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
    nonce_path = DEFAULT_DATA_PATH / "device-nonce.txt"
    if nonce_path.exists():
        with open(nonce_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    nonce = secrets.token_hex(32)
    os.makedirs(nonce_path.parent, exist_ok=True, mode=0o700)
    atomic_write(nonce_path, nonce)
    logger.info("Generated new device nonce and stored in %s", nonce_path)
    return nonce


def find_data_path():
    # find the first path in AGENT_DATA_PATHS that exists and contains the token
    token_path = find_file(AGENT_DATA_PATHS, AGENT_TOKEN_FILENAME)
    if token_path:
        return token_path.parent
    return None


def find_agent_metadata():
    val = None
    logger.debug("Looking for agent metadata in %s", AGENT_DATA_PATHS)
    metadata_path = find_file_multiple_names(
        AGENT_DATA_PATHS,
        [
            AGENT_METADATA_FILENAME,
            f"{AGENT_METADATA_FILENAME}.old",  # legacy recovery
        ],
    )
    if metadata_path:
        logger.debug("Found agent metadata at %s", metadata_path)
        with open(metadata_path, "r", encoding="utf-8") as f:
            val = json.load(f)
    else:
        logger.error("Agent metadata not found")
        return None
    # default populate missing keys
    # first, make sure it's a dict
    if not isinstance(val, dict):
        logger.error("Agent metadata is not a dict")
        val = {}
    # then, populate missing keys
    for key in ["configuration_id", "configuration_commit", "datetime"]:
        val.setdefault(key, None)

    return val
