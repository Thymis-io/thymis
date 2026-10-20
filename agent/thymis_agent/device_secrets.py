"""Secrets the controller deploys onto the device.

They arrive in a `send_secrets` message, encrypted to the SSH host key, and
are kept on disk to be placed again on every start. A freshly flashed image
instead ships them encrypted to the agent token.
"""

import base64
import json
import os
import pathlib
import shutil
from collections.abc import Callable
from typing import cast

from pydantic import ValidationError
from pyrage import decrypt, passphrase, ssh
from thymis_agent import logger
from thymis_agent.host_keys import SSH_HOST_ED25519_KEY_PATH
from thymis_agent.messages import RtESendSecretsMessage
from thymis_agent.storage import find_data_path

ROOT_PASSWORD_HASH_PATH = "/run/thymis/root_password_hash"
SECRETS_MESSAGE_FILENAME = "thymis-secrets-message.json"
SECRETS_INITIAL_FILENAME = "thymis-secrets-initial.json"


def place_secret(
    secret: str,
    path: str,
    owner: str | None,
    group: str | None,
    mode: str | None,
    decrypt_secret: Callable[[bytes], bytes],
) -> None:
    """Decrypt base64 `secret` into `path` and apply ownership and mode."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(decrypt_secret(base64.b64decode(secret)))

    if owner and group:
        shutil.chown(path, owner, group)
    elif owner:
        shutil.chown(path, owner)
    elif group:
        shutil.chown(path, group=group)
    if mode:
        os.chmod(path, int(mode, 8))

    if path == ROOT_PASSWORD_HASH_PATH:
        os.system(
            "/bin/sh -c 'echo \"root:$(cat /run/thymis/root_password_hash)\" | chpasswd -e'"
        )


def place_secrets_from_message(message: RtESendSecretsMessage) -> None:
    """Place the secrets, then keep the message to place them on next start."""
    with open(SSH_HOST_ED25519_KEY_PATH, "rb") as f:
        key = f.read()
    identity = ssh.Identity.from_buffer(key)
    for secret_info in message.secret_infos:
        place_secret(
            message.secrets[secret_info.secret_id],
            secret_info.path,
            secret_info.owner,
            secret_info.group,
            secret_info.mode,
            lambda decoded: decrypt(decoded, [identity]),
        )

    data_path = find_data_path()
    if data_path:
        with open(data_path / SECRETS_MESSAGE_FILENAME, "w", encoding="utf-8") as f:
            f.write(message.model_dump_json())


def place_initial_secrets(secrets_path: pathlib.Path, token: str) -> None:
    """Place the secrets the image was built with."""
    with open(secrets_path, "r", encoding="utf-8") as f:
        s_data = json.loads(f.read())
    secrets_by_id = s_data["secrets"]
    for secret_info in s_data["secret_infos"]:
        place_secret(
            secrets_by_id[secret_info["secret_id"]],
            secret_info["path"],
            secret_info["owner"],
            secret_info["group"],
            secret_info["mode"],
            lambda decoded: passphrase.decrypt(decoded, token),
        )


def place_stored_secrets(token: str | None) -> None:
    """Place the last received secrets, falling back to the initial ones."""
    data_path = find_data_path()
    if not data_path:
        logger.error("Data path not found")
        return
    secrets_path = data_path / SECRETS_MESSAGE_FILENAME
    if secrets_path.exists():
        try:
            with open(secrets_path, "r", encoding="utf-8") as f:
                message = RtESendSecretsMessage.model_validate_json(f.read())
            place_secrets_from_message(message)
        except ValidationError as e:
            logger.error("Failed to validate secrets message: %s", e)
        return
    secrets_path = data_path / SECRETS_INITIAL_FILENAME
    if not secrets_path.exists():
        logger.info("No initial secrets file present (normal for an enrolled device)")
        return
    # the data path is where the token file is, so a token was read from it
    place_initial_secrets(secrets_path, cast(str, token))
