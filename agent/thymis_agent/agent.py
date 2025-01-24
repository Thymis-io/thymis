import json
import logging
import os
import pathlib
import sched
import socket
from typing import Dict, Tuple

import psutil
import requests

logger = logging.getLogger(__name__)

HARDWARE_ID_FILE_PATHS = {
    "pi-serial-number": "/sys/firmware/devicetree/base/serial-number",
    "dmi-board-serial": "/sys/class/dmi/id/board_serial",
    "dmi-product-uuid": "/sys/class/dmi/id/product_uuid",
}

AGENT_TOKEN_FILENAME = "thymis-token.txt"
AGENT_DATA_PATHS = list(
    map(
        pathlib.Path,
        [
            "/boot/firmware",  # raspberry-pi-nix generated sd-cards
            "/boot",  # boot.loader.efi.efiSysMountPoint
        ],
    )
)

AGENT_TOKEN_EXPECTED_FORMAT = (
    "thymis-[0-9a-f]{128}"  # see controller/thymis_controller/task/worker.py `token =`
)

AGENT_METADATA_FILENAME = "thymis-metadata.json"


def find_agent_token():
    for path in AGENT_DATA_PATHS:
        token_path = path / AGENT_TOKEN_FILENAME
        if os.path.exists(token_path):
            with open(token_path, "r", encoding="utf-8") as f:
                return f.read().strip()
    return None


def find_agent_metadata():
    val = None
    logger.debug("Looking for agent metadata in %s", AGENT_DATA_PATHS)
    for path in AGENT_DATA_PATHS:
        metadata_path = path / AGENT_METADATA_FILENAME
        logger.debug("Checking for agent metadata at %s", metadata_path)
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                val = json.load(f)
                break
        else:
            logger.error("Agent metadata not found at %s", metadata_path)
    else:
        logger.error("Agent metadata not found")
        return None
    # default populate missing keys
    # first, make sure it's a dict
    if not isinstance(val, dict):
        logger.error("Agent metadata is not a dict")
        val = {}
    # then, populate missing keys
    for key in ["configuration_id", "configuration_commit"]:
        val.setdefault(key, None)

    return val


agent_token = find_agent_token()
agent_metadata = find_agent_metadata()

if not agent_token:
    logging.error("Agent token not found, continuing without token")
if not agent_metadata:
    logging.error("Agent metadata not found, continuing without metadata")


class AgentScheduler(sched.scheduler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def periodic(self, interval, action, actionargs=()):
        try:
            action(*actionargs)
        except Exception as e:
            logger.error("Action failed: %s", e)
        self.enter(interval, 1, self.periodic, (interval, action, actionargs))

    def retry_if_fails(self, interval, action, actionargs=()):
        try:
            action(*actionargs)
        except Exception as e:
            self.enter(interval, 1, self.retry_if_fails, (interval, action, actionargs))
            logger.error("Action failed, trying again: %s", e)


class Agent:
    controller_host: str

    def __init__(self, path: pathlib.Path, controller_host):
        self.controller_host = controller_host

    def detect_system_config(self) -> Tuple[str, str]:
        return (
            agent_metadata["configuration_id"],
            agent_metadata["configuration_commit"],
        )

    def detect_hostname(self):
        return socket.gethostname()

    def detect_build_hash(self):
        store_path = os.readlink("/run/current-system")
        return store_path[len("/nix/store/") :].split("-")[0]

    def detect_public_key(self):
        with open("/etc/ssh/ssh_host_ed25519_key.pub", "r") as f:
            public_key = f.read().split(" ")
        return public_key[0] + " " + public_key[1]

    def detect_hardware_id(self) -> Dict[str, str]:
        """
        Extracts hardware IDs from the system.

        Returns:
        dict: A dictionary containing the hardware IDs.
        """

        def extract_file_content(path):
            try:
                with open(path, "r") as f:
                    return f.read().replace("\n", "").strip()
            except FileNotFoundError:
                logger.debug("File not found: %s", path)
                return None
            except Exception as e:
                logger.error("Failed to read file: %s", e)
                return None

        hardware_ids = {
            key: extract_file_content(path)
            for key, path in HARDWARE_ID_FILE_PATHS.items()
        }
        return {key: value for key, value in hardware_ids.items() if value}

    def detect_ip_addresses(self):
        def get_ip_addresses(family):
            for interface, snics in psutil.net_if_addrs().items():
                if interface == "lo":
                    continue
                for snic in snics:
                    if snic.family == family:
                        yield snic.address

        ipv4s = set(get_ip_addresses(socket.AF_INET))
        ipv6s = set(get_ip_addresses(socket.AF_INET6))

        return [*ipv4s, *ipv6s]

    def notify(self) -> bool:
        logger.info("Attempting to notify device")

        if not self.controller_host:
            logger.error("Controller host not set")
            raise ValueError("Controller host not set")

        json_data = {
            **({"token": agent_token} if agent_token else {}),
            "hardware_ids": self.detect_hardware_id(),
            "public_key": self.detect_public_key(),
            "deployed_config_id": self.detect_system_config()[0],
            "ip_addresses": self.detect_ip_addresses(),
        }
        logger.info("Sending notify request: %s", json_data)
        response = requests.post(f"{self.controller_host}/agent/notify", json=json_data)

        if response.status_code != 200:
            logger.error(
                "Failed to notify device to controller. Controller returned %s",
                response.status_code,
            )
            raise Exception("Failed to notify device to controller")

        response_json = response.json()

        if response_json.get("force_pubkey_update"):
            logger.info("Controller requested public key update")
            # refresh public key and notify again
            self.update_public_key()
            return self.notify()

        if not response_json.get("success"):
            logger.error(
                "Failed to notify device to controller. Controller returned %s",
                response_json,
            )
            raise Exception("Failed to notify device to controller")

        logger.info("Device notified successfully")

    def report(self):
        logging.info("Reporting state to controller, currently not implemented")

    def update_public_key(self):
        logging.info("Updating public host key")
        paths = ["/etc/ssh/ssh_host_rsa_key", "/etc/ssh/ssh_host_ed25519_key"]
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


def main():
    logging.basicConfig(level=logging.DEBUG)

    controller_host = os.getenv("CONTROLLER_HOST")

    if not controller_host:
        raise ValueError("CONTROLLER_HOST environment variable is required")

    path = pathlib.Path("/var") / "lib" / "thymis" / "agent.json"

    agent = Agent(path, controller_host)
    scheduler = AgentScheduler()

    scheduler.retry_if_fails(10, agent.notify)

    scheduler.run()


if __name__ == "__main__":
    main()
