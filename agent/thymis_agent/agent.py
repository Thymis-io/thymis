import asyncio
import base64
import datetime
import json
import logging
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import uuid
from typing import Dict, List, Literal, Optional, Tuple, Union

import http_network_relay.edge_agent
import http_network_relay.edge_agent as ea
import http_network_relay.pydantic_models as pm
import psutil
import requests
from pydantic import BaseModel, Field
from pyrage import decrypt, passphrase, ssh

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, handlers=[ch])

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


# see https://www.freedesktop.org/software/systemd/man/latest/sd_notify.html
class SystemdNotifier:
    def __init__(self):
        self.NOTIFY_SOCKET = os.getenv("NOTIFY_SOCKET")
        self.already_signaled_ready = False

    def notify(self, message: str):
        if self.NOTIFY_SOCKET is None:
            logger.warning("NOTIFY_SOCKET is not set")
            return

        socket_path = self.NOTIFY_SOCKET
        if socket_path.startswith("@"):
            socket_path = "\0" + socket_path[1:]

        with socket.socket(
            socket.AF_UNIX, socket.SOCK_DGRAM | socket.SOCK_CLOEXEC
        ) as sock:
            sock.connect(self.NOTIFY_SOCKET)
            sock.sendall(message.encode("utf-8"))

    def ready(self):
        if self.already_signaled_ready:
            return
        self.notify("READY=1")
        self.already_signaled_ready = True

    def status(self, message: str):
        self.notify(f"STATUS={message}")


def find_file(paths, filename):
    for path in paths:
        file_path = path / filename
        if os.path.exists(file_path):
            return file_path
    return None


def find_file_multiple_names(paths, filenames):
    for path in paths:
        for filename in filenames:
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
            f"{AGENT_METADATA_FILENAME}.new",
            f"{AGENT_METADATA_FILENAME}.old",
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
    inner: Union["EtRSwitchToNewConfigResultMessage",] = Field(discriminator="kind")


class EtRSwitchToNewConfigResultMessage(BaseModel):
    kind: Literal["switch_to_new_config_result"] = "switch_to_new_config_result"
    task_id: uuid.UUID
    success: Optional[bool] = None  # in v3 dev
    error: Optional[str] = None  # in v3 dev
    config_commit: str | None = None  # in v3 final
    is_activated: bool | None = None  # in v3 final
    switch_success: bool | None = None  # in v3 final
    stdout: str | None = None  # in v3 final
    stderr: str | None = None  # in v3 final


class RelayToAgentMessage(BaseModel):
    # This is a custom message that the relay sends to the agent
    inner: Union[
        "RtEUpdatePublicKeyMessage",
        "RtESwitchToNewConfigMessage",
        "RtESuccesfullySSHConnectedMessage",
        "RtESendSecretsMessage",
    ] = Field(discriminator="kind")


class RtEUpdatePublicKeyMessage(BaseModel):
    kind: Literal["update_public_key"] = "update_public_key"


class RtESwitchToNewConfigMessage(BaseModel):
    kind: Literal["switch_to_new_config"] = "switch_to_new_config"
    new_path_to_config: str
    config_commit: str
    task_id: uuid.UUID


class RtESuccesfullySSHConnectedMessage(BaseModel):
    kind: Literal["successfully_ssh_connected"] = "successfully_ssh_connected"


class SecretForDevice(BaseModel):
    secret_id: uuid.UUID
    path: str
    owner: Optional[str]
    group: Optional[str]
    mode: Optional[str]


class RtESendSecretsMessage(BaseModel):
    kind: Literal["send_secrets"] = "send_secrets"
    secrets: Dict[uuid.UUID, str]
    secret_infos: List[SecretForDevice]


class EdgeAgentToRelayStartMessage(ea.EtRStartMessage):
    token: str
    hardware_ids: Dict[str, str]
    public_key: str
    deployed_config_id: str
    ip_addresses: List[str]
    last_error: Optional[str] = None


def replace_url_protocol_with_ws(url: str) -> str:
    return url.replace("http://", "ws://").replace("https://", "wss://").rstrip("/")


class Agent(ea.EdgeAgent):
    CustomRelayToAgentMessage = RelayToAgentMessage

    controller_host: str

    def __init__(
        self, controller_host, token, agent_metadata, systemd_notifier: SystemdNotifier
    ):
        super().__init__(
            f"{replace_url_protocol_with_ws(controller_host)}/agent/relay",
        )
        self.controller_host = controller_host
        self.token = token
        if not agent_metadata:
            agent_metadata = {}
        self.agent_metadata = agent_metadata
        self.signal_ssh_connected = asyncio.Event()
        self.systemd_notifier = systemd_notifier

    async def handle_custom_relay_message(self, message: RelayToAgentMessage):
        logger.info("Received custom relay message: %s", message.inner.kind)
        match message.inner:
            case RtESuccesfullySSHConnectedMessage():
                logger.info("Successfully SSH connected")
                self.signal_ssh_connected.set()
                self.systemd_notifier.ready()
                self.systemd_notifier.status("Connected to controller")
            case RtEUpdatePublicKeyMessage():
                self.update_public_key()
            case RtESendSecretsMessage():
                self.place_secrets_on_message(message.inner)
            case RtESwitchToNewConfigMessage():
                new_path_to_config = message.inner.new_path_to_config
                current_config = os.readlink("/run/current-system")
                logger.info("Switching to new configuration: %s", new_path_to_config)
                args = [
                    "nix-env",
                    "-p",
                    "/nix/var/nix/profiles/system",
                    "--set",
                    new_path_to_config,
                ]
                proc = await asyncio.create_subprocess_exec(
                    args[0],
                    *args[1:],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    await self.websocket.send(
                        AgentToRelayMessage(
                            inner=EtRSwitchToNewConfigResultMessage(
                                task_id=message.inner.task_id,
                                config_commit=message.inner.config_commit,
                                is_activated=False,
                                switch_success=False,
                                stdout=stdout.decode(),
                                stderr=stderr.decode(),
                            )
                        ).model_dump_json()
                    )
                    raise subprocess.CalledProcessError(
                        proc.returncode, args, stdout, stderr
                    )

                args = [
                    "systemd-run",
                    "-E",
                    "LOCALE_ARCHIVE",
                    "-E",
                    "NIXOS_INSTALL_BOOTLOADER=1",
                    "--collect",
                    "--no-ask-password",
                    "--pipe",
                    "--quiet",
                    "--service-type=exec",
                    "--unit=thymis-nixos-rebuild-switch-to-configuration",
                    "--wait",
                    f"{new_path_to_config}/bin/switch-to-configuration",
                    "switch",
                ]
                proc = await asyncio.create_subprocess_exec(
                    args[0],
                    *args[1:],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()

                # check: "activating the configuration..." and not "Failed to run activate script" in stderr means: is_activated=True
                stderr_str = stderr.decode()
                is_activated = (
                    "activating the configuration..." in stderr_str
                    and "Failed to run activate script" not in stderr_str
                )

                switch_success = proc.returncode == 0

                # switch_success should imply is_activated, if not, then it's a bug
                if switch_success and not is_activated:
                    logger.error(
                        "Switch success but not activated, this is a bug: %s",
                        stderr_str,
                    )
                    raise RuntimeError(
                        "Switch success but not activated, this is a bug",
                        stdout,
                        stderr,
                    )
                try:
                    if is_activated:
                        self.update_config_commit(message.inner.config_commit)
                except Exception as e:
                    logger.error("Failed to update config commit: %s", e)

                async def wait_for_reconnect_and_send_result():
                    websocket = self.websocket
                    await websocket.close()
                    if self.websocket is websocket:
                        await websocket.wait_closed()
                    try:
                        async with asyncio.timeout(60):  # 1 minute timeout
                            await self.signal_connected.wait()
                            await self.signal_ssh_connected.wait()
                    except asyncio.TimeoutError:
                        logger.error("Timeout waiting for connection, rolling back")
                        # rollback
                        args = [
                            "nix-env",
                            "-p",
                            "/nix/var/nix/profiles/system",
                            "--set",
                            current_config,
                        ]
                        proc = await asyncio.create_subprocess_exec(
                            args[0],
                            *args[1:],
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        stdout_l, stderr_l = await proc.communicate()
                        if proc.returncode != 0:
                            logger.error(
                                "Failed to set profile in rollback: %s",
                                stderr_l.decode(),
                            )

                        args = [
                            "systemd-run",
                            "-E",
                            "LOCALE_ARCHIVE",
                            "-E",
                            "NIXOS_INSTALL_BOOTLOADER=1",
                            "--collect",
                            "--no-ask-password",
                            "--pipe",
                            "--quiet",
                            "--service-type=exec",
                            "--unit=thymis-nixos-rebuild-switch-to-configuration-rollback",
                            "--wait",
                            f"{current_config}/bin/switch-to-configuration",
                            "switch",
                        ]

                        proc = await asyncio.create_subprocess_exec(
                            args[0],
                            *args[1:],
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        stdout_l, stderr_l = await proc.communicate()
                        if proc.returncode != 0:
                            logger.error(
                                "Failed to successfully rollback to previous configuration: %s",
                                stderr_l.decode(),
                            )

                        # wait for reconnect
                        await self.signal_connected.wait()
                        await self.signal_ssh_connected.wait()

                        # we are now reconnected with the old configuration

                        await self.websocket.send(
                            AgentToRelayMessage(
                                inner=EtRSwitchToNewConfigResultMessage(
                                    task_id=message.inner.task_id,
                                    config_commit=message.inner.config_commit,
                                    is_activated=False,
                                    switch_success=False,
                                    stdout=stdout.decode() + "\n" + stdout_l.decode(),
                                    stderr=stderr.decode()
                                    + "\n"
                                    + stderr_l.decode()
                                    + "\nReloading old configuration, cannot connect using new configuration",
                                )
                            ).model_dump_json()
                        )

                        return
                    # we are now reconnected
                    await self.websocket.send(
                        AgentToRelayMessage(
                            inner=EtRSwitchToNewConfigResultMessage(
                                task_id=message.inner.task_id,
                                config_commit=message.inner.config_commit,
                                is_activated=is_activated,
                                switch_success=switch_success,
                                stdout=stdout.decode(),
                                stderr=stderr.decode(),
                            )
                        ).model_dump_json()
                    )
                    # wait a few seconds
                    await asyncio.sleep(2)
                    # restart agent using systemd
                    os.system("systemctl restart thymis-agent")

                asyncio.create_task(wait_for_reconnect_and_send_result())

            case _:
                logger.error("Unknown message: %s", message)

    @classmethod
    def place_secrets_on_message(cls, message: RtESendSecretsMessage):
        secrets = message.secrets
        secret_infos = message.secret_infos
        # load /etc/ssh/ssh_host_ed25519_key
        with open("/etc/ssh/ssh_host_ed25519_key", "rb") as f:
            key = f.read()
        identity = ssh.Identity.from_buffer(key)
        for secret_info in secret_infos:
            secret = secrets[secret_info.secret_id]
            path = secret_info.path
            owner = secret_info.owner
            group = secret_info.group
            mode = secret_info.mode
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                decoded = base64.b64decode(secret)
                # use rage to decrypt the secretq
                decrypted = decrypt(decoded, [identity])
                f.write(decrypted)

            if owner or group:
                shutil.chown(
                    path,
                    **{k: v for k, v in {"user": owner, "group": group}.items() if v},
                )
            if mode:
                os.chmod(path, int(mode, 8))

            if path == "/run/thymis/root_password_hash":
                os.system(
                    "/bin/sh -c 'echo \"root:$(cat /run/thymis/root_password_hash)\" | chpasswd -e'"
                )

        # store message on disk at data dir / "thymis-secrets-message.json"
        data_path = find_data_path()
        if data_path:
            with open(
                data_path / "thymis-secrets-message.json", "w", encoding="utf-8"
            ) as f:
                f.write(message.model_dump_json())

    def place_secrets_on_start(self, token: str):
        # use message if there, if not
        # try using thymis-secrets-initial.json and decrypting using token,

        # Create and write rsyslog config
        controller_host_port = (
            "443" if self.controller_host.startswith("https") else "80"
        )
        controller_host_domain = self.controller_host.split("://")[1].split("/")[0]
        controller_host_path = self.controller_host.split("://")[1].partition("/")[2]
        restpath = f"{controller_host_path}/agent/logs".lstrip("/")
        use_https = "on" if self.controller_host.startswith("https") else "off"
        rsyslog_config = f"""
        module(load="imuxsock")
        module(load="imklog")
        module(load="omhttp")
        template(name="tpl_omhttp_json" type="list") {{
            constant(value="{{")   property(name="msg"           outname="message"   format="jsonfr")
            constant(value=",")   property(name="syslogfacility" outname="facility" format="jsonfr" datatype="number")
            constant(value=",")   property(name="syslogseverity" outname="severity" format="jsonfr" datatype="number")
            constant(value=",")   property(name="syslogtag"     outname="syslogtag" format="jsonfr")
            constant(value=",")   property(name="programname"   outname="programname" format="jsonfr")
            constant(value=",")   property(name="hostname"      outname="host"      format="jsonfr")
            constant(value=",")   property(name="timereported"  outname="timestamp" format="jsonfr" dateFormat="rfc3339" date.inUTC="on")
            constant(value=",")   property(name="uuid"         outname="uuid"      format="jsonfr")
            constant(value="}}")
        }}
        template(name="tpl_echo" type="string" string="%msg%")
        ruleset(name="rs_retry_forever") {{
            action(
                type="omhttp"
                template="tpl_omhttp_json"
                httpheaders=[
                    "X-Thymis-Ssh-Pubkey: {self.detect_public_key()}",
                    "X-Thymis-Token: {token}",
                    "X-Thymis-Hostname: {self.detect_hostname()}"
                ]
                server="{controller_host_domain}"
                serverport="{controller_host_port}"
                restpath="{restpath}"
                useHttps="{use_https}"
                batch="on"
                batch.format="jsonarray"
                retry="on"
                retry.ruleset="rs_omhttp_retry"
                restpathtimeout="5000"
            )
        }}
        ruleset(name="rs_omhttp_retry") {{
            action(
                type="omhttp"
                template="tpl_echo"
                httpheaders=[
                    "X-Thymis-Ssh-Pubkey: {self.detect_public_key()}",
                    "X-Thymis-Token: {token}",
                    "X-Thymis-Hostname: {self.detect_hostname()}"
                ]
                server="{controller_host_domain}"
                serverport="{controller_host_port}"
                restpath="{restpath}"
                useHttps="{use_https}"
                batch="on"
                batch.format="jsonarray"
                batch.maxsize="1"
                action.resumeRetryCount="3"
                action.resumeInterval="20"
                errorfile="/var/log/rsyslog-error.log"
                restpathtimeout="5000"
            )
        }}

        call rs_retry_forever
        """

        os.makedirs("/etc/rsyslog.d", exist_ok=True, mode=0o755)
        with open("/etc/rsyslog.d/thymis.conf", "w", encoding="utf-8") as f:
            f.write(rsyslog_config)

        data_path = find_data_path()
        if not data_path:
            logger.error("Data path not found")
            return
        secrets_path = data_path / "thymis-secrets-message.json"
        if secrets_path.exists():
            with open(secrets_path, "r", encoding="utf-8") as f:
                message = RtESendSecretsMessage.model_validate_json(f.read())
            self.place_secrets_on_message(message)
            return
        secrets_path = data_path / "thymis-secrets-initial.json"
        if not secrets_path.exists():
            logger.error("Secrets not found")
            return
        with open(secrets_path, "r", encoding="utf-8") as f:
            s_file = f.read()
        s_data = json.loads(s_file)
        secrets = s_data["secrets"]
        secret_infos = s_data["secret_infos"]
        # decrypt secrets using token

        for secret_info in secret_infos:
            secret = secrets[secret_info["secret_id"]]
            path = secret_info["path"]
            owner = secret_info["owner"]
            group = secret_info["group"]
            mode = secret_info["mode"]

            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                decoded = base64.b64decode(secret)
                # use rage to decrypt the secret
                decrypted = passphrase.decrypt(decoded, token)
                f.write(decrypted)
            if owner or group:
                shutil.chown(
                    path,
                    **{k: v for k, v in {"user": owner, "group": group}.items() if v},
                )
            if mode:
                os.chmod(path, int(mode, 8))

            if path == "/run/thymis/root_password_hash":
                os.system(
                    "/bin/sh -c 'echo \"root:$(cat /run/thymis/root_password_hash)\" | chpasswd -e'"
                )

    async def on_connected(self):
        self.systemd_notifier.status("Connected to relay")

    async def create_start_message(self, last_error: Optional[str] = None):
        return EdgeAgentToRelayStartMessage(
            token=self.token,
            hardware_ids=self.detect_hardware_id(),
            public_key=self.detect_public_key(),
            deployed_config_id=self.detect_system_config()[0],
            ip_addresses=self.detect_ip_addresses(),
            last_error=last_error,
        )

    async def on_connection_closed(self):
        self.signal_ssh_connected.clear()
        self.systemd_notifier.status("Connection closed, reconnecting...")
        await super().on_connection_closed()

    def update_config_commit(self, new_commit: str):
        self.agent_metadata["configuration_commit"] = new_commit
        metadata_path = find_file(AGENT_DATA_PATHS, AGENT_METADATA_FILENAME)
        if metadata_path:
            # with open(metadata_path, "w", encoding="utf-8") as f:
            #     json.dump(self.agent_metadata, f)
            new_path = f"{metadata_path}.new"
            old_path = f"{metadata_path}.old"
            # first, write to a new file
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(self.agent_metadata, f)
            # then, rename the old file
            os.rename(metadata_path, old_path)
            # then, rename the new file
            os.rename(new_path, metadata_path)
            # then, remove the old file
            os.remove(old_path)

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
        with open("/etc/ssh/ssh_host_ed25519_key.pub", "r", encoding="utf-8") as f:
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
                with open(path, "r", encoding="utf-8") as f:
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


def set_minimum_time(datetime_str: str):
    time = datetime.datetime.now()
    metadata_time = datetime.datetime.fromisoformat(datetime_str)
    if time < metadata_time:
        subprocess.run(["date", "-s", datetime_str])


def main():
    agent_metadata = find_agent_metadata()

    if not agent_metadata:
        logging.error("Agent metadata not found, continuing without metadata")

    controller_host = os.getenv("CONTROLLER_HOST")

    if not controller_host:
        raise ValueError("CONTROLLER_HOST environment variable is required")

    logger.setLevel(logging.INFO)
    if agent_metadata:
        set_minimum_time(agent_metadata["datetime"])

    systemd_notifier = SystemdNotifier()

    load_controller_public_key_into_root_authorized_keys()
    agent_token = find_agent_token()
    agent = Agent(controller_host, agent_token, agent_metadata, systemd_notifier)
    agent.place_secrets_on_start(agent_token)
    if "--just-place-secrets" not in sys.argv:
        asyncio.run(agent.async_main())


if __name__ == "__main__":
    main()
