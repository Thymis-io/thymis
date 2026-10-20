import logging
import os

SSH_HOST_KEY_PATHS = ["/etc/ssh/ssh_host_rsa_key", "/etc/ssh/ssh_host_ed25519_key"]


def detect_public_key() -> str:
    with open("/etc/ssh/ssh_host_ed25519_key.pub", "r", encoding="utf-8") as f:
        public_key = f.read().split(" ")
    return public_key[0] + " " + public_key[1]


def rotate_host_keys() -> None:
    logging.info("Updating public host key")
    paths = SSH_HOST_KEY_PATHS
    # rename the old keys to .old.N where N is a number such that the file does not exist
    # generate new keys by restarting the sshd service

    # find N
    n = 0
    while any(os.path.exists(f"{path}.old.{n}") for path in paths):
        n += 1

    for path in paths:
        os.rename(path, f"{path}.old.{n}")

    # restart sshd
    os.system("systemctl restart sshd")

    logging.info("Public host key updated")
