import asyncio
import os
import subprocess
from typing import Any, NoReturn, cast

import http_network_relay.edge_agent as ea
from pydantic import BaseModel
from thymis_agent import logger
from thymis_agent.device_secrets import place_secrets_from_message
from thymis_agent.host_keys import detect_public_key, rotate_host_keys
from thymis_agent.hostname import (
    DEFAULT_HOSTNAME,
    apply_hostname,
    read_hostname,
    store_hostname,
)
from thymis_agent.messages import (
    AgentToRelayMessage,
    EdgeAgentToRelayStartMessage,
    EtRNetworkInterfacesMessage,
    EtRSwitchToNewConfigResultMessage,
    RelayToAgentMessage,
    RtESendSecretsMessage,
    RtESuccesfullySSHConnectedMessage,
    RtESwitchToNewConfigMessage,
    RtEUpdateHostnameMessage,
    RtEUpdatePublicKeyMessage,
)
from thymis_agent.nixos_switch import (
    ROLLBACK_UNIT,
    SWITCH_UNIT,
    interpret_switch_result,
    read_current_system,
    run_process,
    set_system_profile_args,
    switch_needs_reboot,
    switch_to_configuration_args,
)
from thymis_agent.rsyslog import reload_rsyslog, write_rsyslog_config
from thymis_agent.storage import update_agent_metadata
from thymis_agent.system_info import (
    collect_metrics,
    detect_hardware_id,
    detect_network_interfaces,
    detect_ram_bytes,
    init_metrics,
)
from thymis_agent.systemd import SystemdNotifier
from websockets import ConnectionClosed
from websockets.asyncio.client import ClientConnection


def replace_url_protocol_with_ws(url: str) -> str:
    return url.replace("http://", "ws://").replace("https://", "wss://").rstrip("/")


class Agent(ea.EdgeAgent):
    CustomRelayToAgentMessage = RelayToAgentMessage

    controller_host: str

    def __init__(
        self,
        controller_host: str,
        token: str,
        agent_metadata: dict[str, Any] | None,
        systemd_notifier: SystemdNotifier,
        manage_hostname: bool = False,
        default_hostname: str = DEFAULT_HOSTNAME,
    ) -> None:
        super().__init__(
            f"{replace_url_protocol_with_ws(controller_host)}/agent/relay",
        )
        self.controller_host = controller_host
        self.token = token
        self.agent_metadata = agent_metadata or {}
        self.signal_ssh_connected = asyncio.Event()
        self.systemd_notifier = systemd_notifier
        self.manage_hostname = manage_hostname
        self.default_hostname = default_hostname

    async def async_main(self) -> NoReturn:
        asyncio.create_task(self.collect_and_send_metrics())
        asyncio.create_task(self.collect_and_send_network_interfaces())
        await super().async_main()

    async def handle_custom_relay_message(self, message: BaseModel) -> None:
        # the base class parses relay messages as `CustomRelayToAgentMessage`
        inner = cast(RelayToAgentMessage, message).inner
        logger.info("Received custom relay message: %s", inner.kind)
        match inner:
            case RtESuccesfullySSHConnectedMessage():
                self.on_ssh_connected()
            case RtEUpdatePublicKeyMessage():
                rotate_host_keys()
            case RtESendSecretsMessage():
                place_secrets_from_message(inner)
            case RtESwitchToNewConfigMessage():
                await self.switch_to_new_config(inner)
            case RtEUpdateHostnameMessage():
                await self.update_hostname(inner.hostname)
            case _:
                logger.error("Unknown message: %s", message)

    def on_ssh_connected(self) -> None:
        logger.info("Successfully SSH connected")
        self.signal_ssh_connected.set()
        self.systemd_notifier.ready()
        self.systemd_notifier.status("Connected to controller")

    async def send_switch_result(
        self,
        message: RtESwitchToNewConfigMessage,
        *,
        is_activated: bool,
        switch_success: bool,
        stdout: str,
        stderr: str,
        reboot_required: bool | None = None,
    ) -> None:
        # the base class types the connection as optional; switch results are
        # only sent while connected
        await cast(ClientConnection, self.websocket).send(
            AgentToRelayMessage(
                inner=EtRSwitchToNewConfigResultMessage(
                    task_id=message.task_id,
                    configuration_id=message.configuration_id,
                    config_commit=message.config_commit,
                    is_activated=is_activated,
                    switch_success=switch_success,
                    stdout=stdout,
                    stderr=stderr,
                    reboot_required=reboot_required,
                )
            ).model_dump_json()
        )

    async def switch_to_new_config(self, message: RtESwitchToNewConfigMessage) -> None:
        """Switch to the new configuration, then report the result once the
        agent has reconnected from it, rolling back if it cannot."""
        new_path_to_config = message.new_path_to_config
        current_config = read_current_system()
        logger.info("Switching to new configuration: %s", new_path_to_config)
        args = set_system_profile_args(new_path_to_config)
        returncode, stdout, stderr = await run_process(args)
        if returncode != 0:
            await self.send_switch_result(
                message,
                is_activated=False,
                switch_success=False,
                stdout=stdout.decode(),
                stderr=stderr.decode(),
            )
            raise subprocess.CalledProcessError(returncode, args, stdout, stderr)

        returncode, stdout, stderr = await run_process(
            switch_to_configuration_args(new_path_to_config, SWITCH_UNIT)
        )

        stderr_str = stderr.decode()
        is_activated, switch_success = interpret_switch_result(returncode, stderr_str)
        reboot_required = switch_needs_reboot(returncode, is_activated)
        if reboot_required:
            logger.warning(
                "switch-to-configuration exited %s after activating the "
                "configuration (some units failed to reload/restart); "
                "treating the switch as successful, a reboot is "
                "required to finish the update: %s",
                returncode,
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
                    message.configuration_id,
                    message.config_commit,
                )
        except Exception as e:
            logger.error("Failed to update config commit: %s", e)

        asyncio.create_task(
            self.wait_for_reconnect_and_send_result(
                message,
                current_config,
                is_activated,
                switch_success,
                reboot_required,
                stdout,
                stderr,
            )
        )

    async def wait_for_reconnect_and_send_result(
        self,
        message: RtESwitchToNewConfigMessage,
        current_config: str,
        is_activated: bool,
        switch_success: bool,
        reboot_required: bool,
        stdout: bytes,
        stderr: bytes,
    ) -> None:
        # the switch was requested over this connection, so it is set
        websocket = cast(ClientConnection, self.websocket)
        self.signal_connected.clear()
        await websocket.close()
        try:
            async with asyncio.timeout(60):  # 1 minute timeout
                await self.signal_connected.wait()
                await self.signal_ssh_connected.wait()
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for connection, rolling back")
            await self.rollback_and_send_result(message, current_config, stdout, stderr)
            return
        await self.send_switch_result(
            message,
            is_activated=is_activated,
            switch_success=switch_success,
            reboot_required=reboot_required,
            stdout=stdout.decode(),
            stderr=stderr.decode(),
        )
        await asyncio.sleep(2)
        # pick up the agent from the new configuration
        os.system("systemctl restart thymis-agent")

    async def rollback_and_send_result(
        self,
        message: RtESwitchToNewConfigMessage,
        current_config: str,
        stdout: bytes,
        stderr: bytes,
    ) -> None:
        returncode, stdout_l, stderr_l = await run_process(
            set_system_profile_args(current_config)
        )
        if returncode != 0:
            logger.error(
                "Failed to set profile in rollback: %s",
                stderr_l.decode(),
            )

        returncode, stdout_l, stderr_l = await run_process(
            switch_to_configuration_args(current_config, ROLLBACK_UNIT, quiet=True)
        )
        if returncode != 0:
            logger.error(
                "Failed to successfully rollback to previous configuration: %s",
                stderr_l.decode(),
            )

        await self.signal_connected.wait()
        await self.signal_ssh_connected.wait()
        await self.send_switch_result(
            message,
            is_activated=False,
            switch_success=False,
            stdout=stdout.decode() + "\n" + stdout_l.decode(),
            stderr=stderr.decode()
            + "\n"
            + stderr_l.decode()
            + "\nReloading old configuration, cannot connect using new configuration",
        )

    async def update_hostname(self, hostname: str | None) -> None:
        if not self.manage_hostname:
            logger.info("Ignoring hostname update: MANAGE_HOSTNAME is not set")
            return
        store_hostname(hostname)
        if await asyncio.to_thread(
            apply_hostname, read_hostname(self.default_hostname)
        ):
            # update rsyslog so X-Thymis-Hostname reflects the new hostname
            await self.update_rsyslog()

    async def update_rsyslog(self) -> None:
        if not write_rsyslog_config(self.controller_host, self.token):
            return
        await reload_rsyslog()

    async def create_start_message(
        self, last_error: str | None = None
    ) -> EdgeAgentToRelayStartMessage:
        return EdgeAgentToRelayStartMessage(
            token=self.token,
            hardware_ids=detect_hardware_id(),
            public_key=detect_public_key(),
            deployed_config_id=self.agent_metadata.get("configuration_id"),
            deployed_config_commit=self.agent_metadata.get("configuration_commit"),
            network_interfaces=detect_network_interfaces(),
            ram_bytes=detect_ram_bytes(),
            last_error=last_error,
        )

    async def on_connection_closed(self) -> None:
        self.signal_ssh_connected.clear()
        self.systemd_notifier.status("Connection closed, reconnecting...")
        await super().on_connection_closed()

    async def collect_and_send_metrics(self) -> None:
        """Collect system metrics every 60s and send to controller."""
        init_metrics()
        while not self.websocket:
            await asyncio.sleep(10)
        while True:
            try:
                if self.websocket:
                    msg = AgentToRelayMessage(inner=collect_metrics())
                    await self.websocket.send(msg.model_dump_json())
            except ConnectionClosed:
                pass
            except Exception as e:
                logger.error("Failed to collect/send metrics: %s", e)
            await asyncio.sleep(60)

    async def collect_and_send_network_interfaces(self) -> None:
        """Detect network interface changes every 20 s; send only when state differs."""
        last_sent: list[dict[str, Any]] | None = None
        while not self.websocket:
            await asyncio.sleep(10)
        while True:
            try:
                if self.websocket:
                    current = detect_network_interfaces()
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

    def update_config_metadata(self, new_config_id: str, new_commit: str) -> None:
        self.agent_metadata["configuration_id"] = new_config_id
        self.agent_metadata["configuration_commit"] = new_commit
        update_agent_metadata(self.agent_metadata)
