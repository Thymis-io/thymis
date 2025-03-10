import base64
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional, assert_never

import http_network_relay.network_relay as nr
import paramiko
import sqlalchemy.orm
import thymis_agent.agent as agent
import thymis_controller.crud.agent_token as crud_agent_token
import thymis_controller.crud.deployment_info as crud_deployment_info
import thymis_controller.crud.hardware_device as crud_hardware_device
import thymis_controller.models.task as models_task
from fastapi import WebSocket
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from pyrage import ssh
from thymis_controller.config import global_settings

if TYPE_CHECKING:
    from thymis_controller.notifications import NotificationManager
    from thymis_controller.task.controller import TaskController

logger = logging.getLogger(__name__)


def verify_alive_with_ssh_host_key_and_connection_perms(
    public_key: str,
    host: str | None = None,
    port: int | None = None,
    sock: Any | None = None,
    username: str = "root",
    pkey: paramiko.PKey = None,
):
    class ExpectedHostKeyNotFound(Exception):
        pass

    class CheckForExpectedHostKey(paramiko.MissingHostKeyPolicy):
        def __init__(self, expected_key):
            self.expected_key = expected_key

        def missing_host_key(self, client, hostname, key: paramiko.PKey):
            actual_key = f"{key.get_name()} {key.get_base64()}"
            if actual_key != self.expected_key:
                raise ExpectedHostKeyNotFound()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(CheckForExpectedHostKey(public_key))
    try:
        client.connect(
            hostname=host,
            port=port,
            sock=sock,
            username=username,
            pkey=pkey,
        )
    except ExpectedHostKeyNotFound:
        logger.error("Host key mismatch for %s", host)
        return False
    except paramiko.AuthenticationException:
        logger.error("Authentication failed for %s", host)
        return False
    except paramiko.SSHException as e:
        logger.error("SSH error for %s: %s", host, e)
        return False

    # run a command to verify the connection
    etc_os_release = client.exec_command("cat /etc/os-release")[1].read()
    logger.debug("Remote /etc/os-release: %s", etc_os_release)

    client.close()
    logger.debug("Verified host key for %s", host)

    return True


class NetworkRelay(nr.NetworkRelay):
    CustomAgentToRelayMessage = agent.AgentToRelayMessage
    CustomAgentToRelayStartMessage = agent.EdgeAgentToRelayStartMessage

    def __init__(self, db_engine, notification_manager):
        super().__init__()
        self.db_engine = db_engine
        self.public_key_to_connection_id = {}
        self.connection_id_to_public_key = {}
        self.connection_id_to_start_message: dict[
            str, agent.EdgeAgentToRelayStartMessage
        ] = {}
        self.task_controller: Optional["TaskController"] = None
        self.notification_manager: "NotificationManager" = notification_manager

    async def handle_custom_agent_message(
        self, message: agent.AgentToRelayMessage, connection_id: str
    ):
        match message.inner:
            case agent.EtRSwitchToNewConfigResultMessage():
                inner = message.inner
                # compat: v3 dev to v3 final
                if hasattr(inner, "success") and inner.success is not None:
                    # agent is old, update message to new format
                    inner = agent.EtRSwitchToNewConfigResultMessage(
                        switch_success=inner.success,
                        stdout="",
                        stderr=inner.error or "",
                        is_activated=inner.success,
                        config_commit=None,
                        task_id=inner.task_id,
                    )
                # update deployment_info
                with sqlalchemy.orm.Session(self.db_engine) as db_session:
                    deployment_info = crud_deployment_info.get_by_ssh_public_key(
                        db_session, self.connection_id_to_public_key[connection_id]
                    )
                    if not deployment_info:
                        logger.error(
                            "Deployment info not found for public key %s",
                            self.connection_id_to_public_key[connection_id],
                        )
                        raise ValueError("Deployment info not found")
                    if inner.is_activated:
                        crud_deployment_info.update(
                            db_session,
                            deployment_info[0].id,
                            deployed_config_commit=inner.config_commit,
                        )
                self.task_controller.executor.send_message_to_task(
                    inner.task_id,
                    models_task.ControllerToRunnerTaskUpdate(
                        inner=models_task.AgentSwitchToNewConfigurationResult(
                            success=inner.switch_success,
                            stdout=inner.stdout,
                            stderr=inner.stderr,
                        )
                    ),
                )
            case _:
                assert_never(message.inner)

    async def handle_edge_agent_message(self, message, message_outer, connection_id):
        # if is keep alive message, update last seen in deployment_info and hardware_device

        if isinstance(message, nr.EtRKeepAliveMessage):
            with sqlalchemy.orm.Session(self.db_engine) as db_session:
                deployment_info = crud_deployment_info.get_by_ssh_public_key(
                    db_session, self.connection_id_to_public_key[connection_id]
                )
                if not deployment_info:
                    logger.error(
                        "Deployment info not found for public key %s",
                        self.connection_id_to_public_key[connection_id],
                    )
                    raise ValueError("Deployment info not found")
                deployment_info = crud_deployment_info.update(
                    db_session,
                    deployment_info[0].id,
                    last_seen=datetime.now(timezone.utc),
                )
                if deployment_info.hardware_devices:
                    for hardware_device in deployment_info.hardware_devices:
                        hardware_device.last_seen = datetime.now(timezone.utc)
                # update clients
                db_session.commit()
            # notify browsers to update /api/all_connected_deployment_info
            self.notification_manager.broadcast_invalidate_notification(
                ["/api/all_deployment_infos", "/api/all_connected_deployment_info"]
            )

        return await super().handle_edge_agent_message(
            message, message_outer, connection_id
        )

    async def get_agent_msg_loop_permission_and_create_connection_id(
        self, start_message: BaseModel, edge_agent_connection: WebSocket
    ) -> str | None:
        if not isinstance(start_message, agent.EdgeAgentToRelayStartMessage):
            return None
        # check for valid token
        with sqlalchemy.orm.Session(self.db_engine) as db_session:
            if not crud_agent_token.check_token_validity(
                db_session, start_message.token
            ):
                logging.error(
                    "Agent with start message %s has invalid token %s",
                    start_message,
                    start_message.token,
                )
                return None

        # check for valid public key, we don't want to have multiple simultaneous agent connections with the same public key
        # so we check if the public key is already in use by another agent
        # check in self.registered_agent_connections
        if (
            start_message.public_key in self.public_key_to_connection_id
            and (
                other_con_id := self.public_key_to_connection_id.get(
                    start_message.public_key
                )
            )
            and (other_con := self.registered_agent_connections.get(other_con_id))
        ):
            # could be dangerous, could just be closed
            # check if we can ssh connect to the host
            # if we can, then we have to notify our agent
            # to rekey
            # if we can't, then we can just remove the connection
            # and add the new one
            verify_alive = await run_in_threadpool(
                verify_alive_with_ssh_host_key_and_connection_perms,
                start_message.public_key,
                sock=await self.create_connection(other_con_id, "localhost", 22, "tcp"),
                username="root",
                pkey=paramiko.PKey.from_path(
                    global_settings.PROJECT_PATH / "id_thymis"
                ),
            )
            if verify_alive:
                # notify the agent to rekey
                await self.registered_agent_connections[
                    self.public_key_to_connection_id[start_message.public_key]
                ].send_text(
                    agent.RelayToAgentMessage(
                        inner=agent.RtEUpdatePublicKeyMessage()
                    ).model_dump_json()
                )
                # and close the connection
                return None
            else:
                # connection is not healthy, just close it
                await other_con.close()
                # and remove the ssh public key reservation
                other_con_public_key = self.connection_id_to_public_key[other_con_id]
                del self.public_key_to_connection_id[other_con_public_key]
                del self.connection_id_to_public_key[other_con_id]
                del self.connection_id_to_start_message[other_con_id]

        connection_id = str(uuid.uuid4())
        self.public_key_to_connection_id[start_message.public_key] = connection_id
        self.connection_id_to_public_key[connection_id] = start_message.public_key
        self.connection_id_to_start_message[connection_id] = start_message
        return connection_id

    async def accept_ws_and_start_msg_loop_for_edge_agents(
        self,
        edge_agent_connection: WebSocket,
    ):
        res = await super().accept_ws_and_start_msg_loop_for_edge_agents(
            edge_agent_connection
        )
        if res is None:
            return
        msg_loop, connection_id = res
        # we can establish ssh connections here
        # check that the public key is valid

        public_key_valid = await run_in_threadpool(
            verify_alive_with_ssh_host_key_and_connection_perms,
            self.connection_id_to_public_key[connection_id],
            sock=await self.create_connection(connection_id, "localhost", 22, "tcp"),
            username="root",
            pkey=paramiko.PKey.from_path(global_settings.PROJECT_PATH / "id_thymis"),
        )

        if not public_key_valid:
            logger.error(
                "Cannot access agent with public key %s via ssh over websocket",
                self.connection_id_to_public_key[connection_id],
            )
            await edge_agent_connection.close()
            return

        # the agent should also rekey if the public key has a deployment_info with a different hardware_device
        with sqlalchemy.orm.Session(self.db_engine) as db_session:
            # current state: device is reachable via ssh and has a valid public key

            same_public_key = crud_deployment_info.get_by_ssh_public_key(
                db_session, self.connection_id_to_public_key[connection_id]
            )

            # if more than 2 deployment_infos have the same public key, fail
            if len(same_public_key) >= 2:
                logger.error(
                    "Agent with public key %s notifies controller from %s with public key that is already in use by %d devices"
                    "we do not handle this case yet",
                    self.connection_id_to_public_key[connection_id],
                    edge_agent_connection.client.host,
                    len(same_public_key),
                )
                return

            overlapping_devices = crud_hardware_device.find_overlapping_hardware_ids(
                db_session,
                self.connection_id_to_start_message[connection_id].hardware_ids,
            )

            # count the number of overlapping devices
            overlapping_devices_count = len(overlapping_devices)
            if overlapping_devices_count >= 2:
                # fail for now
                logger.error(
                    "Agent with public key %s notifies controller with hardware ids %s which overlap with %d devices",
                    self.connection_id_to_public_key[connection_id],
                    self.connection_id_to_start_message[connection_id].hardware_ids,
                    overlapping_devices_count,
                )
                logger.error(
                    "Overlapping devices: %s",
                    overlapping_devices,
                )
                return

            if (
                len(same_public_key) == 1
                and not overlapping_devices
                and len(self.connection_id_to_start_message[connection_id].hardware_ids)
                > 0
            ):
                # this branch means: if your underlying hardware has changed, you need to update your public key
                logger.info(
                    "Force public key update for agent %s",
                    edge_agent_connection.client.host,
                )
                self.public_key_to_connection_id[
                    self.connection_id_to_public_key[connection_id]
                ] = None
                self.connection_id_to_public_key[connection_id] = None
                await self.registered_agent_connections[connection_id].send_text(
                    agent.RelayToAgentMessage(
                        inner=agent.RtEUpdatePublicKeyMessage()
                    ).model_dump_json()
                )
                return

            # create database entries
            deployment_info = crud_deployment_info.create_or_update_by_public_key(
                db_session,
                self.connection_id_to_public_key[connection_id],
                self.connection_id_to_start_message[connection_id].deployed_config_id,
                None,
            )

            deployment_info_id = deployment_info.id

            if len(self.connection_id_to_start_message[connection_id].hardware_ids) > 0:
                hardware_device = crud_hardware_device.create_or_update(
                    db_session,
                    self.connection_id_to_start_message[connection_id].hardware_ids,
                    deployment_info.id,
                )
            else:
                logger.warning(
                    "Agent %s has no hardware ids, not creating a hardware device",
                    connection_id,
                )

            if not self.connection_id_to_start_message[
                connection_id
            ].last_error or not (
                "Input tag 'successfully_ssh_connected' found using 'kind' does not match any of the expected tags"
                in self.connection_id_to_start_message[connection_id].last_error
                or "Input tag 'keep_alive' found using 'kind' does not match any of the expected tags"
                in self.connection_id_to_start_message[connection_id].last_error
            ):
                logger.info(
                    "Agent %s connected successfully, sending message to agent",
                    connection_id,
                )
                secrets = []
                secret_infos = []
                state = self.task_controller.project.read_state()
                config = next(
                    config
                    for config in state.configs
                    if config.identifier
                    == self.connection_id_to_start_message[
                        connection_id
                    ].deployed_config_id
                )
                modules = self.task_controller.project.get_modules_for_config(
                    state, config
                )
                for module, settings in modules:
                    for secret_type, secret in module.register_secret_settings(
                        settings, self.task_controller.project
                    ):
                        secrets.append(uuid.UUID(secret))
                        secret_infos.append(
                            agent.SecretForDevice(
                                secret_id=secret,
                                path=secret_type.on_device_path,
                                owner=secret_type.on_device_owner,
                                group=secret_type.on_device_group,
                                mode=secret_type.on_device_mode,
                            )
                        )
                processed_secrets = self.task_controller.project.get_processed_secrets(
                    db_session,
                    secrets,
                    ssh.Recipient.from_str(
                        self.connection_id_to_public_key[connection_id]
                    ),
                )

                await edge_agent_connection.send_text(
                    agent.RelayToAgentMessage(
                        inner=agent.RtESendSecretsMessage(
                            secrets={
                                k: base64.b64encode(v).decode("utf-8")
                                for k, v in processed_secrets.items()
                            },
                            secret_infos=secret_infos,
                        )
                    ).model_dump_json()
                )

                await edge_agent_connection.send_text(
                    agent.RelayToAgentMessage(
                        inner=agent.RtESuccesfullySSHConnectedMessage(
                            deployment_info_id=deployment_info_id
                        )
                    ).model_dump_json()
                )

        async def msg_loop_but_close_connection_at_end():
            try:
                await msg_loop
            finally:
                # close the connection
                if connection_id in self.connection_id_to_public_key:
                    public_key = self.connection_id_to_public_key[connection_id]
                    del self.public_key_to_connection_id[public_key]
                    del self.connection_id_to_public_key[connection_id]
                    del self.connection_id_to_start_message[connection_id]

        self.notification_manager.broadcast_invalidate_notification(
            [
                "/api/all_deployment_infos",
                "/api/all_connected_deployment_info",
                "/api/deployment_infos_by_config_id",
                "/api/connected_deployment_infos_by_config_id",
            ]
        )

        return msg_loop_but_close_connection_at_end(), connection_id

    async def get_access_client_permission(
        self, start_message: nr.AtRStartMessage, access_client_connection
    ):
        with sqlalchemy.orm.Session(self.db_engine) as db_session:
            if not crud_agent_token.check_access_client_token_validity(
                db_session, start_message.secret, start_message.connection_target
            ):
                logging.error(
                    "Access client with start message %s has invalid token %s",
                    start_message,
                    start_message.secret,
                )
                return False
        return True

    async def get_agent_connection_id_for_access_client(self, connection_target):
        with sqlalchemy.orm.Session(self.db_engine) as db_session:
            deployment_info = crud_deployment_info.get_by_id(
                db_session, uuid.UUID(connection_target)
            )
            if not deployment_info:
                raise ValueError("No deployment info found for connection target")
            public_key = deployment_info.ssh_public_key
            if not public_key:
                raise ValueError("No public key found for deployment info")
            if public_key not in self.public_key_to_connection_id:
                raise ValueError("No connection found for public key")
            return self.public_key_to_connection_id[public_key]

    if "RUNNING_IN_PLAYWRIGHT" in os.environ:

        async def disconnect_and_ban_all_connections(self, db_session):
            agent_connections = self.registered_agent_connections.copy()
            for connection_id, connection in agent_connections.items():
                start_message = self.connection_id_to_start_message[connection_id]
                # ban the token
                crud_agent_token.revoke_access_client_token(
                    db_session, start_message.token
                )
                await connection.close()
                if connection_id in self.connection_id_to_public_key:
                    public_key = self.connection_id_to_public_key[connection_id]
                    del self.public_key_to_connection_id[public_key]
                if connection_id in self.connection_id_to_public_key:
                    del self.connection_id_to_public_key[connection_id]
                if connection_id in self.connection_id_to_start_message:
                    del self.connection_id_to_start_message[connection_id]
            # delete all deployment infos
            crud_deployment_info.delete_all(db_session)
