import asyncio
import base64
import datetime
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
from datetime import timezone
from typing import Any, Dict, List, Optional

import http_network_relay.edge_agent as ea
import psutil
from pydantic import ValidationError
from pyrage import decrypt, passphrase, ssh
from thymis_agent import logger
from thymis_agent.constants import (
    AGENT_DATA_PATHS,
    AGENT_METADATA_FILENAME,
    DEFAULT_DATA_PATH,
    DEFAULT_HOSTNAME,
    DEVICE_HOSTNAME_FILENAME,
    HARDWARE_ID_FILE_PATHS,
    HOSTNAME_PATH,
)
from thymis_agent.files import atomic_write, find_file
from thymis_agent.messages import (
    AgentToRelayMessage,
    EdgeAgentToRelayStartMessage,
    EtRMetricsMessage,
    EtRNetworkInterfacesMessage,
    EtRSwitchToNewConfigResultMessage,
    RelayToAgentMessage,
    RtESendSecretsMessage,
    RtESuccesfullySSHConnectedMessage,
    RtESwitchToNewConfigMessage,
    RtEUpdateHostnameMessage,
    RtEUpdatePublicKeyMessage,
)
from thymis_agent.storage import find_data_path
from thymis_agent.switch import interpret_switch_result, switch_needs_reboot
from thymis_agent.systemd import SystemdNotifier
from websockets import ConnectionClosed


def replace_url_protocol_with_ws(url: str) -> str:
    return url.replace("http://", "ws://").replace("https://", "wss://").rstrip("/")


class Agent(ea.EdgeAgent):
    CustomRelayToAgentMessage = RelayToAgentMessage

    controller_host: str

    def __init__(
        self,
        controller_host,
        token,
        agent_metadata,
        systemd_notifier: SystemdNotifier,
        manage_hostname: bool = False,
        default_hostname: str = DEFAULT_HOSTNAME,
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
        self.manage_hostname = manage_hostname
        self.default_hostname = default_hostname

    async def async_main(self):
        asyncio.create_task(self.collect_and_send_metrics())
        asyncio.create_task(self.collect_and_send_network_interfaces())
        await super().async_main()

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
                                configuration_id=message.inner.configuration_id,
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

                stderr_str = stderr.decode()
                is_activated, switch_success = interpret_switch_result(
                    proc.returncode, stderr_str
                )
                reboot_required = switch_needs_reboot(proc.returncode, is_activated)
                if reboot_required:
                    logger.warning(
                        "switch-to-configuration exited %s after activating the "
                        "configuration (some units failed to reload/restart); "
                        "treating the switch as successful, a reboot is "
                        "required to finish the update: %s",
                        proc.returncode,
                        stderr_str,
                    )

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
                        self.update_config_metadata(
                            message.inner.configuration_id,
                            message.inner.config_commit,
                        )
                except Exception as e:
                    logger.error("Failed to update config commit: %s", e)

                async def wait_for_reconnect_and_send_result():
                    websocket = self.websocket
                    self.signal_connected.clear()
                    await websocket.close()
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
                                    configuration_id=message.inner.configuration_id,
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
                                configuration_id=message.inner.configuration_id,
                                config_commit=message.inner.config_commit,
                                is_activated=is_activated,
                                switch_success=switch_success,
                                reboot_required=reboot_required,
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

            case RtEUpdateHostnameMessage():
                if not self.manage_hostname:
                    logger.info("Ignoring hostname update: MANAGE_HOSTNAME is not set")
                else:
                    self.store_hostname(message.inner.hostname)
                    if await asyncio.to_thread(
                        self.apply_hostname, self.read_hostname()
                    ):
                        # update rsyslog so X-Thymis-Hostname reflects the new hostname
                        await self.update_rsyslog()
            case _:
                logger.error("Unknown message: %s", message)

    def store_hostname(self, hostname: str | None):
        path = DEFAULT_DATA_PATH / DEVICE_HOSTNAME_FILENAME
        try:
            if hostname:
                os.makedirs(DEFAULT_DATA_PATH, exist_ok=True, mode=0o700)
                atomic_write(path, hostname + "\n", mode=0o644)
            else:
                path.unlink(missing_ok=True)
        except OSError as e:
            logger.error("Failed to store device hostname: %s", e)

    def read_hostname(self) -> str:
        """The stored device hostname, else the deployed default."""
        try:
            device_hostname_path = DEFAULT_DATA_PATH / DEVICE_HOSTNAME_FILENAME
            stored = device_hostname_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            stored = ""
        except OSError as e:
            logger.error("Failed to read device hostname: %s", e)
            stored = ""
        return stored.strip() or self.default_hostname

    def apply_hostname(self, hostname: str) -> bool:
        """Set `hostname`. Returns True if the hostname changed."""
        try:
            return self._set_hostname(hostname)
        except OSError as e:
            logger.error("Failed to apply hostname %r: %s", hostname, e)
            return False

    def _set_hostname(self, hostname: str) -> bool:
        changed = False
        try:
            static_hostname = HOSTNAME_PATH.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            static_hostname = None
        if static_hostname != hostname:
            atomic_write(HOSTNAME_PATH, hostname + "\n", mode=0o644)
            changed = True
        if socket.gethostname() != hostname:
            socket.sethostname(hostname)
            changed = True
        if changed:
            logger.info("Hostname set to: %s", hostname)
        return changed

    async def update_rsyslog(self):
        if not self._write_rsyslog_config():
            return
        proc = await asyncio.create_subprocess_exec(
            "systemctl",
            "reload",
            "syslog.service",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error(
                "Failed to reload syslog.service: %s",
                stderr.decode(),
            )
        else:
            logger.info("syslog.service reloaded successfully")

    @classmethod
    def place_secrets_on_message(cls, message: RtESendSecretsMessage):
        # load /etc/ssh/ssh_host_ed25519_key
        with open("/etc/ssh/ssh_host_ed25519_key", "rb") as f:
            key = f.read()
        identity = ssh.Identity.from_buffer(key)
        for secret_info in message.secret_infos:
            secret = message.secrets[secret_info.secret_id]
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

    def _write_rsyslog_config(self) -> bool:
        """Write /etc/rsyslog.d/thymis.conf. Returns True if the file changed."""
        if not self.token:
            return False

        controller_host_domain_and_maybe_port = self.controller_host.split("://")[
            1
        ].split("/")[0]
        controller_host_domain = controller_host_domain_and_maybe_port.split(":")[0]
        if ":" in controller_host_domain_and_maybe_port:
            controller_host_port = controller_host_domain_and_maybe_port.split(":")[1]
        else:
            controller_host_port = (
                "443" if self.controller_host.startswith("https") else "80"
            )
        controller_host_path = self.controller_host.split("://")[1].partition("/")[2]
        restpath = f"{controller_host_path}/agent/logs".lstrip("/")
        use_https = "on" if self.controller_host.startswith("https") else "off"
        token = self.token
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
        if os.path.exists("/etc/rsyslog.d/thymis.conf"):
            with open("/etc/rsyslog.d/thymis.conf", "r", encoding="utf-8") as f:
                existing_config = f.read()
        else:
            existing_config = None
        if existing_config == rsyslog_config:
            return False
        with open("/etc/rsyslog.d/thymis.conf", "w", encoding="utf-8") as f:
            f.write(rsyslog_config)
        return True

    def place_secrets_on_start(self, token: str):
        # use message if there, if not
        # try using thymis-secrets-initial.json and decrypting using token,
        if token is not None:
            changed = self._write_rsyslog_config()
            if changed:
                logger.info("Rsyslog config changed, reloading")
                if "--just-place-secrets" in sys.argv:
                    os.makedirs("/run/nixos", exist_ok=True, mode=0o755)
                    with open(
                        "/run/nixos/activation-reload-list", "a+", encoding="utf-8"
                    ) as f:
                        f.write("syslog.service\n")
                else:
                    subprocess.run(
                        ["systemctl", "reload", "syslog.service"], check=False
                    )

        data_path = find_data_path()
        if not data_path:
            logger.error("Data path not found")
            return
        secrets_path = data_path / "thymis-secrets-message.json"
        if secrets_path.exists():
            try:
                with open(secrets_path, "r", encoding="utf-8") as f:
                    message = RtESendSecretsMessage.model_validate_json(f.read())
                self.place_secrets_on_message(message)
            except ValidationError as e:
                logger.error("Failed to validate secrets message: %s", e)
            return
        secrets_path = data_path / "thymis-secrets-initial.json"
        if not secrets_path.exists():
            logger.info(
                "No initial secrets file present (normal for an enrolled device)"
            )
            return
        with open(secrets_path, "r", encoding="utf-8") as f:
            s_file = f.read()
        s_data = json.loads(s_file)
        secrets_by_id = s_data["secrets"]
        secret_infos = s_data["secret_infos"]
        # decrypt secrets using token

        for secret_info in secret_infos:
            secret = secrets_by_id[secret_info["secret_id"]]
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

    async def create_start_message(self, last_error: Optional[str] = None):
        return EdgeAgentToRelayStartMessage(
            token=self.token,
            hardware_ids=self.detect_hardware_id(),
            public_key=self.detect_public_key(),
            deployed_config_id=self.detect_configuration_id(),
            deployed_config_commit=self.detect_configuration_commit(),
            network_interfaces=self.detect_network_interfaces(),
            ram_bytes=self.detect_ram_bytes(),
            last_error=last_error,
        )

    async def on_connection_closed(self):
        self.signal_ssh_connected.clear()
        self.systemd_notifier.status("Connection closed, reconnecting...")
        await super().on_connection_closed()

    async def collect_and_send_metrics(self):
        """Collect system metrics every 60s and send to controller."""
        psutil.cpu_percent(interval=None)  # call once to initialize
        while not self.websocket:
            await asyncio.sleep(10)
        while True:
            try:
                if self.websocket:
                    msg = AgentToRelayMessage(
                        inner=EtRMetricsMessage(
                            timestamp=datetime.datetime.now(timezone.utc),
                            cpu_percent=psutil.cpu_percent(interval=None),
                            ram_percent=psutil.virtual_memory().percent,
                            disk_percent=psutil.disk_usage("/").percent,
                        )
                    )
                    await self.websocket.send(msg.model_dump_json())
            except ConnectionClosed:
                pass
            except Exception as e:
                logger.error("Failed to collect/send metrics: %s", e)
            await asyncio.sleep(60)

    async def collect_and_send_network_interfaces(self):
        """Detect network interface changes every 20 s; send only when state differs."""
        last_sent: Optional[List[Dict[str, Any]]] = None
        while not self.websocket:
            await asyncio.sleep(10)
        while True:
            try:
                if self.websocket:
                    current = self.detect_network_interfaces()
                    if current != last_sent:
                        msg = AgentToRelayMessage(
                            inner=EtRNetworkInterfacesMessage(
                                network_interfaces=current,
                            )
                        )
                        await self.websocket.send(msg.model_dump_json())
                        last_sent = current
            except ConnectionClosed:
                pass
            except Exception as e:
                logger.error("Failed to collect/send network interfaces: %s", e)
            await asyncio.sleep(20)

    def update_config_metadata(self, new_config_id: str, new_commit: str):
        self.agent_metadata["configuration_id"] = new_config_id
        self.agent_metadata["configuration_commit"] = new_commit
        metadata_path = find_file(AGENT_DATA_PATHS, AGENT_METADATA_FILENAME)
        if metadata_path:
            atomic_write(metadata_path, json.dumps(self.agent_metadata), mode=0o644)

    def detect_configuration_id(self) -> str | None:
        return self.agent_metadata.get("configuration_id", None)

    def detect_configuration_commit(self) -> str | None:
        return self.agent_metadata.get("configuration_commit", None)

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

    def detect_ram_bytes(self) -> Optional[int]:
        """Detect total RAM in bytes using psutil."""
        try:
            return psutil.virtual_memory().total
        except Exception as e:
            logger.debug("Failed to detect RAM: %s", e)
            return None

    def detect_network_interfaces(self):
        interfaces = {}
        for interface, snics in psutil.net_if_addrs().items():
            if interface == "lo":
                continue
            if interface not in interfaces:
                interfaces[interface] = {
                    "interface": interface,
                    "ipv4_addresses": [],
                    "ipv6_addresses": [],
                    "mac_address": None,
                }
            for snic in snics:
                if snic.family == socket.AF_INET:
                    interfaces[interface]["ipv4_addresses"].append(snic.address)
                elif snic.family == socket.AF_INET6:
                    interfaces[interface]["ipv6_addresses"].append(snic.address)
                elif snic.family == psutil.AF_LINK:
                    interfaces[interface]["mac_address"] = snic.address
        return sorted(
            (
                {
                    "interface": iface["interface"],
                    "ipv4_addresses": sorted(iface["ipv4_addresses"]),
                    "ipv6_addresses": sorted(iface["ipv6_addresses"]),
                    "mac_address": iface["mac_address"],
                }
                for iface in interfaces.values()
            ),
            key=lambda x: x["interface"],
        )

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
