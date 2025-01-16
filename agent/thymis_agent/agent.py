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
        config_id = None
        commit_hash = None
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("IMAGE_ID="):
                    config_id = line.split("=")[1].strip().replace('"', "")
                    if config_id == "":
                        config_id = None
                if line.startswith("IMAGE_VERSION="):
                    commit_hash = line.split("=")[1].strip().replace('"', "")
                    if commit_hash == "":
                        commit_hash = None

        return config_id, commit_hash

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

        return {
            key: extract_file_content(path)
            for key, path in HARDWARE_ID_FILE_PATHS.items()
        }

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

        config_id, commit_hash = self.detect_system_config()

        json_data = {
            "commit_hash": commit_hash,
            "config_id": config_id,
            "hardware_ids": self.detect_hardware_id(),
            "public_key": self.detect_public_key(),
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
