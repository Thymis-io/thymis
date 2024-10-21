import dataclasses
import json
import logging
import os
import pathlib
import sched
import socket
from dataclasses import dataclass
from typing import List

import psutil
import requests

logger = logging.getLogger(__name__)


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


class Storage:
    path: pathlib.Path

    def __init__(self, path: pathlib.Path):
        if path is None:
            raise ValueError(
                "path is required"
            )  # TODO: why does vscode say this is unreachable?

        self.path = path

    def read_state(self):
        if not self.path.exists():
            # create file
            logger.info("Creating state file")
            os.makedirs(self.path.parent, exist_ok=True)
            state = DeviceState()
            # write state to the file
            self.write_state(state)
            return state
        # read the state from the json file to a dictionary
        text = self.path.read_text()
        # parse the json to DeviceState
        return DeviceState(**json.loads(text))

    def write_state(self, state: "DeviceState"):
        json_text = json.dumps(dataclasses.asdict(state))
        self.path.write_text(json_text)


@dataclass
class DeviceState:
    registered: bool = False
    hostname: str | None = None
    init_build_hash: str | None = None
    current_build_hash: str | None = None
    public_key: str | None = None
    ip_addresses: List[str] | None = None


class Agent:
    controller_host: str
    storage: Storage
    state: DeviceState

    def __init__(self, path: pathlib.Path, controller_host):
        self.controller_host = controller_host
        self.storage = Storage(path)

        self.state = self.storage.read_state()

        if not self.state.hostname:
            self.state.hostname = self.detect_hostname()

        if not self.state.init_build_hash:
            self.state.init_build_hash = self.detect_build_hash()
            self.state.current_build_hash = self.state.init_build_hash

        # if not self.state.public_key:
        self.state.public_key = self.detect_public_key()

        if not self.state.ip_addresses:
            self.state.ip_addresses = self.detect_ip_addresses()

        self._write_state()
        logging.info("Agent initialized with state %s", self.state)

    @property
    def registered(self):
        return self.state.registered

    def _write_state(self):
        self.storage.write_state(self.state)

    def detect_hostname(self):
        return socket.gethostname()

    def detect_build_hash(self):
        store_path = os.readlink("/run/current-system")
        return store_path[len("/nix/store/") :].split("-")[0]

    def detect_public_key(self):
        with open("/etc/ssh/ssh_host_ed25519_key.pub", "r") as f:
            public_key = f.read().split(" ")
        return public_key[0] + " " + public_key[1]

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

    def registered_only(func):
        def wrapper(self, *args, **kwargs):
            if self.registered:
                return func(self, *args, **kwargs)
            else:
                return None

        return wrapper

    def register(self) -> bool:
        logger.info("Attempting to register device")

        if not self.controller_host:
            logger.error("Controller host not set")
            raise ValueError("Controller host not set")

        json_data = {
            "build_hash": self.state.init_build_hash,
            "public_key": self.state.public_key,
            "ip_addresses": self.detect_ip_addresses(),
        }

        response = requests.post(
            f"{self.controller_host}/agent/register", json=json_data
        )

        if response.status_code != 200:
            logger.error(
                "Failed to register device. Controller returned %s",
                response.status_code,
            )
            raise Exception("Failed to register device")

        self.state.registered = True
        self._write_state()
        logger.info("Device registered successfully")

    def _send_heartbeat(self, ip_addresses: List[str]):
        logger.info("Sending heartbeat to controller")
        json_data = {
            "public_key": self.state.public_key,
            "ip_addresses": ip_addresses,
        }

        response = requests.post(
            f"{self.controller_host}/agent/heartbeat", json=json_data
        )

        if response.status_code != 200:
            logger.error(
                "Failed to send heartbeat. Controller returned %s",
                response.status_code,
            )
            raise Exception("Failed to send heartbeat")

        logger.info("Heartbeat sent successfully")

    @registered_only
    def heartbeat(self, reason: str = None):
        ip_addresses = self.detect_ip_addresses()
        self._send_heartbeat(ip_addresses)

    @registered_only
    def check_for_ip_change(self):
        ip_addresses = self.detect_ip_addresses()
        if self.state.ip_addresses != ip_addresses:
            logger.info("IP addresses changed, reporting to controller")
            self.heartbeat("ip_change")
            self.state.ip_addresses = ip_addresses
            self._write_state()

    @registered_only
    def check_for_deploy(self):
        current_build_hash = self.detect_build_hash()
        if self.state.current_build_hash != current_build_hash:
            logger.info("Build hash changed, reporting to controller")
            self.heartbeat("deploy")
            self.state.current_build_hash = current_build_hash
            self._write_state()

    def report(self):
        logging.info("Reporting state to controller, currently not implemented")


def main():
    logging.basicConfig(level=logging.DEBUG)

    REPORT_INTERVAL = 60
    TIMEOUT_INTERVAL = 600
    CHECK_INTERVAL = 20

    controller_host = os.getenv("CONTROLLER_HOST")

    if not controller_host:
        raise ValueError("CONTROLLER_HOST environment variable is required")

    path = pathlib.Path("/var") / "lib" / "thymis" / "agent.json"

    agent = Agent(path, controller_host)
    scheduler = AgentScheduler()

    # TODO maybe implement any way to reregister if the controller loses the registration
    if not agent.registered:
        scheduler.retry_if_fails(10, agent.register)

    scheduler.retry_if_fails(10, agent.heartbeat, ["restart"])
    scheduler.periodic(CHECK_INTERVAL, agent.check_for_ip_change)
    scheduler.periodic(CHECK_INTERVAL, agent.check_for_deploy)
    scheduler.periodic(TIMEOUT_INTERVAL, agent.heartbeat, ["timeout"])

    scheduler.periodic(REPORT_INTERVAL, agent.report)

    scheduler.run()


if __name__ == "__main__":
    main()
