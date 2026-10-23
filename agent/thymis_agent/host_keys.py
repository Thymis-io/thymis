"""The device's SSH host keys, which identify it to the controller."""

import os

from thymis_agent import logger

SSH_HOST_ED25519_KEY_PATH = "/etc/ssh/ssh_host_ed25519_key"
SSH_HOST_KEY_PATHS = ["/etc/ssh/ssh_host_rsa_key", SSH_HOST_ED25519_KEY_PATH]


def detect_public_key() -> str:
    """The ed25519 public key, without its comment."""
    with open(f"{SSH_HOST_ED25519_KEY_PATH}.pub", "r", encoding="utf-8") as f:
        public_key = f.read().split(" ")
    return public_key[0] + " " + public_key[1]


def rotate_host_keys() -> None:
    """Move the host keys to `<key>.old.N` and let sshd generate new ones."""
    logger.info("Updating public host key")
    n = 0
    while any(os.path.exists(f"{path}.old.{n}") for path in SSH_HOST_KEY_PATHS):
        n += 1
    for path in SSH_HOST_KEY_PATHS:
        os.rename(path, f"{path}.old.{n}")
    os.system("systemctl restart sshd")
    logger.info("Public host key updated")
