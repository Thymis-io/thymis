import os

import requests
from thymis_agent import logger
from thymis_agent.constants import (
    AGENT_DATA_PATHS,
    CONTROLLER_PUBLIC_KEY_FILENAME,
    DEFAULT_DATA_PATH,
    ROOT_AUTHORIZED_KEYS_PATH,
)
from thymis_agent.files import atomic_write, find_file
from thymis_agent.storage import find_data_path


def load_controller_public_key_into_root_authorized_keys() -> None:
    controller_public_key_path = find_file(
        AGENT_DATA_PATHS, CONTROLLER_PUBLIC_KEY_FILENAME
    )
    if not controller_public_key_path:
        logger.error("Controller public key file not found")
        return
    with open(controller_public_key_path, "r", encoding="utf-8") as f:
        controller_public_key = f.read().strip()
    if not controller_public_key:
        logger.error(
            "Controller public key file %s is empty", controller_public_key_path
        )
        return
    separator = ""
    if os.path.exists(ROOT_AUTHORIZED_KEYS_PATH):
        with open(ROOT_AUTHORIZED_KEYS_PATH, "r", encoding="utf-8") as f:
            contents = f.read()
        if controller_public_key in contents.splitlines():
            return
        if contents and not contents.endswith("\n"):
            separator = "\n"
    os.makedirs(os.path.dirname(ROOT_AUTHORIZED_KEYS_PATH), exist_ok=True, mode=0o700)
    with open(ROOT_AUTHORIZED_KEYS_PATH, "a+", encoding="utf-8") as f:
        f.write(f"{separator}{controller_public_key}\n")


def revoke_key_from_root_authorized_keys(public_key: str) -> None:
    if not os.path.exists(ROOT_AUTHORIZED_KEYS_PATH):
        return
    with open(ROOT_AUTHORIZED_KEYS_PATH, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    kept = [line for line in lines if line.strip() != public_key]
    if len(kept) == len(lines):
        return
    atomic_write(
        ROOT_AUTHORIZED_KEYS_PATH,
        "".join(f"{line}\n" for line in kept),
        mode=0o600,
    )
    logger.info("Removed superseded controller public key from root authorized_keys")


def store_controller_public_key(controller_public_key: str) -> None:
    controller_public_key = controller_public_key.strip()
    path = find_file(AGENT_DATA_PATHS, CONTROLLER_PUBLIC_KEY_FILENAME)
    previous_key = None
    if path:
        with open(path, "r", encoding="utf-8") as f:
            previous_key = f.read().strip()
    else:
        data_path = find_data_path() or DEFAULT_DATA_PATH
        os.makedirs(data_path, exist_ok=True, mode=0o700)
        path = data_path / CONTROLLER_PUBLIC_KEY_FILENAME
    if previous_key == controller_public_key:
        return
    atomic_write(path, f"{controller_public_key}\n", mode=0o644)
    logger.info("Stored controller public key at %s", path)
    if previous_key:
        revoke_key_from_root_authorized_keys(previous_key)


def refresh_controller_public_key(controller_host: str, token: str) -> None:
    """Best-effort: the controller may rotate its key, but a device that cannot
    reach it still has to boot with whatever key it was given last."""
    url = f"{controller_host.rstrip('/')}/agent/controller-ssh-pubkey"
    try:
        response = requests.get(url, headers={"x-thymis-token": token}, timeout=10)
        response.raise_for_status()
        controller_public_key = response.json()["controller_ssh_pubkey"]
    except (requests.exceptions.RequestException, KeyError, ValueError) as e:
        logger.warning("Could not fetch controller public key from %s: %s", url, e)
        return
    if controller_public_key:
        store_controller_public_key(controller_public_key)
