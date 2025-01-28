import asyncio
import json
import logging
import os
import pathlib
import socket
from typing import Dict, List, Literal, Tuple, Union

import http_network_relay.edge_agent
import http_network_relay.edge_agent as ea
import http_network_relay.pydantic_models as pm
import psutil
import requests
from pydantic import BaseModel, Field

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
CONTROLLER_PUBLIC_KEY_FILENAME = "thymis-controller-ssh-pubkey.txt"


def find_file(paths, filename):
    for path in paths:
        file_path = path / filename
        if os.path.exists(file_path):
            return file_path
    return None


def find_agent_token():
    token_path = find_file(AGENT_DATA_PATHS, AGENT_TOKEN_FILENAME)
    if token_path:
        with open(token_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def find_agent_metadata():
    val = None
    logger.debug("Looking for agent metadata in %s", AGENT_DATA_PATHS)
    metadata_path = find_file(AGENT_DATA_PATHS, AGENT_METADATA_FILENAME)
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
    for key in ["configuration_id", "configuration_commit"]:
        val.setdefault(key, None)

    return val


def load_controller_public_key_into_root_authorized_keys():
    # only if not already there at /root/.ssh/authorized_keys
    controller_public_key_path = find_file(
        AGENT_DATA_PATHS, CONTROLLER_PUBLIC_KEY_FILENAME
    )
    if not controller_public_key_path:
        logger.error("Controller public key file not found")
        return
    with open(controller_public_key_path, "r", encoding="utf-8") as f:
        controller_public_key = f.read()
    if os.path.exists("/root/.ssh/authorized_keys"):
        with open("/root/.ssh/authorized_keys", "r", encoding="utf-8") as f:
            contents = f.read()
        if controller_public_key in contents:
            return
    os.makedirs("/root/.ssh", exist_ok=True, mode=0o700)
    with open("/root/.ssh/authorized_keys", "a+", encoding="utf-8") as f:
        f.write(f"{controller_public_key}\n")


class AgentToRelayMessage(BaseModel):
    # This is a custom message that the agent sends to the relay
    pass


class RelayToAgentMessage(BaseModel):
    # This is a custom message that the relay sends to the agent
    inner: Union["RtEUpdatePublicKeyMessage",] = Field(discriminator="kind")


class RtEUpdatePublicKeyMessage(BaseModel):
    kind: Literal["update_public_key"] = "update_public_key"


class EdgeAgentToRelayStartMessage(ea.EtRStartMessage):
    token: str
    hardware_ids: Dict[str, str]
    public_key: str
    deployed_config_id: str
    ip_addresses: List[str]


def replace_url_protocol_with_ws(url: str) -> str:
    return url.replace("http://", "ws://").replace("https://", "wss://")


class Agent(ea.EdgeAgent):
    CustomRelayToAgentMessage = RelayToAgentMessage

    controller_host: str

    def __init__(self, controller_host, token, agent_metadata):
        super().__init__(
            f"{replace_url_protocol_with_ws(controller_host)}/agent/relay",
        )
        self.controller_host = controller_host
        self.token = token
        self.agent_metadata = agent_metadata

    async def handle_custom_relay_message(self, message: RelayToAgentMessage):
        match message.inner:
            case RtEUpdatePublicKeyMessage():
                self.update_public_key()
            case _:
                logger.error("Unknown message: %s", message)

    async def create_start_message(self):
        return EdgeAgentToRelayStartMessage(
            token=self.token,
            hardware_ids=self.detect_hardware_id(),
            public_key=self.detect_public_key(),
            deployed_config_id=self.detect_system_config()[0],
            ip_addresses=self.detect_ip_addresses(),
        )

    def detect_system_config(self) -> Tuple[str, str]:
        return (
            self.agent_metadata["configuration_id"],
            self.agent_metadata["configuration_commit"],
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
    agent_metadata = find_agent_metadata()

    if not agent_metadata:
        logging.error("Agent metadata not found, continuing without metadata")

    logging.basicConfig(level=logging.DEBUG)

    controller_host = os.getenv("CONTROLLER_HOST")

    if not controller_host:
        raise ValueError("CONTROLLER_HOST environment variable is required")

    load_controller_public_key_into_root_authorized_keys()
    agent_token = find_agent_token()
    agent = Agent(controller_host, agent_token, agent_metadata)
    asyncio.run(agent.async_main())


if __name__ == "__main__":
    main()
