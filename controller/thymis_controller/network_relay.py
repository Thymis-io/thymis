import logging
import uuid
from typing import Any

import http_network_relay.network_relay as nr
import paramiko
import sqlalchemy.orm
import thymis_agent.agent as agent
import thymis_controller.crud.agent_token as crud_agent_token
import thymis_controller.crud.deployment_info as crud_deployment_info
import thymis_controller.crud.hardware_device as crud_hardware_device
from fastapi import WebSocket
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from thymis_controller.config import global_settings

logger = logging.getLogger(__name__)
# @router.post("/notify")
# def device_notify(
#     device_notify_request: models.DeviceNotifyRequest,
#     request: Request,
#     db_session: SessionAD,
#     project: ProjectAD,
# ):
#     logger.info("Device notify request: %s", device_notify_request)
#     request_source = (
#         request.client
#     )  # see --forwarded-allow-ips for uvicorn configuration
#     # check for token using db
#     if device_notify_request.token:
#         if not crud.agent_token.check_token_validity(
#             db_session, device_notify_request.token
#         ):
#             logger.error(
#                 "Device with public key %s notifies controller with invalid token %s",
#                 device_notify_request.public_key,
#                 device_notify_request.token,
#             )
#             raise HTTPException(
#                 status_code=400
#             )  # do not reveal information to misbehaving devices
#     else:
#         # no token is actually semi-fine, we log everything but we do not create any database entries
#         logger.warning(
#             "Device with public key %s notifies controller without token "
#             "possibly due to an outdated agent version, an attacker or a misconfiguration "
#             "you will still see all checks logged, however no database entries are created",
#             device_notify_request.public_key,
#         )
#     logger.debug(
#         "Device with public key %s notifies controller from %s",
#         device_notify_request.public_key,
#         request_source.host,
#     )

#     # check if device is reachable using device supplied public key
#     reachable_deployed_host: str | None = determine_first_host_with_key(
#         hosts=[request.client.host, *device_notify_request.ip_addresses],
#         public_key=device_notify_request.public_key,
#     )

#     if not reachable_deployed_host:
#         logger.error(
#             "Device with public key %s notifies controller from %s with unreachable host",
#             device_notify_request.public_key,
#             request_source.host,
#         )
#         raise HTTPException(status_code=400)

#     # verify ssh key
#     verified_ssh = project.verify_ssh_host_key_and_creds(
#         reachable_deployed_host,
#         device_notify_request.public_key,
#         port=22,
#         username="root",
#         pkey=paramiko.PKey.from_path(global_settings.PROJECT_PATH / "id_thymis"),
#     )

#     if not verified_ssh:
#         logger.error(
#             "Device with public key %s notifies controller from %s with unreachable host %s",
#             device_notify_request.public_key,
#             request_source.host,
#             reachable_deployed_host,
#         )

#         raise HTTPException(status_code=400)

#     hardware_ids = {
#         key: value for key, value in device_notify_request.hardware_ids.items() if value
#     }
#     # check: does any of my hardware ids overlap with any in the db
#     overlapping_devices = crud.hardware_device.find_overlapping_hardware_ids(
#         db_session, hardware_ids
#     )

#     # count the number of overlapping devices
#     overlapping_devices_count = len(overlapping_devices)
#     if overlapping_devices_count >= 2:
#         # fail for now
#         logger.error(
#             "Device with public key %s notifies controller with hardware ids %s which overlap with %d devices",
#             device_notify_request.public_key,
#             hardware_ids,
#             overlapping_devices_count,
#         )
#         logger.error(
#             "Overlapping devices: %s",
#             overlapping_devices,
#         )
#         raise HTTPException(status_code=400)

#     # count has to be 0 or 1, both are fine

#     # current state: device is reachable via ssh and has a valid public key
#     # identity of the hardware device is either completely new or already known, but not overlapping with multiple devices

#     # now: check wether any other deployment_info has the same public key
#     same_public_key = crud.deployment_info.get_by_ssh_public_key(
#         db_session, device_notify_request.public_key
#     )

#     # if more than 2 devices have the same public key, fail
#     if len(same_public_key) >= 2:
#         logger.error(
#             "Device with public key %s notifies controller from %s with public key that is already in use by %d devices"
#             "we do not handle this case yet",
#             device_notify_request.public_key,
#             request_source.host,
#             len(same_public_key),
#         )
#         raise HTTPException(status_code=400)

#     force_pubkey_update = len(same_public_key) == 1 and not overlapping_devices

#     if force_pubkey_update:
#         logger.info("Force public key update for device %s", reachable_deployed_host)
#         # this branch means: if your underlying hardware has changed, you need to update your public key
#         return {"force_pubkey_update": True}

#     # create or update deployment_info
#     if device_notify_request.token:
#         deployment_info = crud.deployment_info.create_or_update_by_public_key(
#             db_session,
#             device_notify_request.public_key,
#             device_notify_request.deployed_config_id,
#             reachable_deployed_host,
#         )
#         hardware_device = crud.hardware_device.create_or_update(
#             db_session,
#             hardware_ids,
#             deployment_info.id,
#         )

#     project.update_known_hosts(db_session)

#     return {"success": True}

# class NetworkRelay:
#     CustomAgentToRelayMessage: Type[BaseModel] = None

#     def __init__(self, credentials):
#         self.agent_connections = []
#         self.registered_agent_connections = {}  # name -> connection

#         self.credentials = credentials

#     async def ws_for_edge_agents(self, websocket: WebSocket):
#         await websocket.accept()
#         self.agent_connections.append(websocket)
#         start_message_json_data = await websocket.receive_text()
#         start_message = EdgeAgentToRelayMessage.model_validate_json(
#             start_message_json_data
#         ).inner
#         eprint(f"Message received from agent: {start_message}")
#         if not isinstance(start_message, EtRStartMessage):
#             eprint(f"Unknown message received from agent: {start_message}")
#             return
#         #  check if we know the agent
#         if start_message.name not in self.credentials["edge-agents"]:
#             eprint(f"Unknown agent: {start_message.name}")
#             # close the connection
#             await websocket.close()
#             return

#         # check if the secret is correct
#         if self.credentials["edge-agents"][start_message.name] != start_message.secret:
#             eprint(f"Invalid secret for agent: {start_message.name}")
#             # close the connection
#             await websocket.close()
#             return

#         # check if the agent is already registered
#         if start_message.name in self.registered_agent_connections:
#             # check wether the other websocket is still open, if not remove it
#             if self.registered_agent_connections[start_message.name].closed:
#                 del self.registered_agent_connections[start_message.name]
#             else:
#                 eprint(f"Agent already registered: {start_message.name}")
#                 # close the connection
#                 await websocket.close()
#                 return

#         self.registered_agent_connections[start_message.name] = websocket
#         eprint(f"Registered agent connection: {start_message.name}")

#         while True:
#             try:
#                 json_data = await websocket.receive_text()
#             except WebSocketDisconnect:
#                 eprint(f"Agent disconnected: {start_message.name}")
#                 del self.registered_agent_connections[start_message.name]
#                 break
#             try:
#                 message = EdgeAgentToRelayMessage.model_validate_json(json_data).inner
#             except ValidationError as e:
#                 if self.CustomAgentToRelayMessage is None:
#                     raise e
#                 message = self.CustomAgentToRelayMessage.model_validate_json(
#                     json_data
#                 )  # pylint: disable=E1101
#             eprint(f"Message received from agent: {message}", only_debug=True)
#             if isinstance(message, EtRInitiateConnectionErrorMessage):
#                 eprint(
#                     f"Received initiate connection error message from agent: {message}"
#                 )
#                 await self.handle_initiate_connection_error_message(message)
#             elif isinstance(message, EtRInitiateConnectionOKMessage):
#                 eprint(f"Received initiate connection OK message from agent: {message}")
#                 await self.handle_initiate_connection_ok_message(message)
#             elif isinstance(message, EtRTCPDataMessage):
#                 eprint(
#                     f"Received TCP data message from agent: {message}", only_debug=True
#                 )
#                 await self.handle_tcp_data_message(message)
#             elif isinstance(message, EtRConnectionResetMessage):
#                 eprint(f"Received connection reset message from agent: {message}")
#                 await self.handle_connection_reset_message(message)
#             elif self.CustomAgentToRelayMessage is not None and isinstance(
#                 message, self.CustomAgentToRelayMessage
#             ):
#                 await self.handle_custom_agent_message(message)
#             else:
#                 eprint(f"Unknown message received from agent: {message}")

#     async def handle_custom_agent_message(self, message: BaseModel):
#         raise NotImplementedError()

#     async def handle_initiate_connection_error_message(
#         self, message: EtRInitiateConnectionErrorMessage
#     ):
#         raise NotImplementedError()

#     async def handle_initiate_connection_ok_message(
#         self, message: EtRInitiateConnectionOKMessage
#     ):
#         raise NotImplementedError()

#     async def handle_tcp_data_message(self, message: EtRTCPDataMessage):
#         raise NotImplementedError()


#     async def handle_connection_reset_message(self, message: EtRConnectionResetMessage):
#         raise NotImplementedError()
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

    def __init__(self, db_engine):
        super().__init__()
        self.db_engine = db_engine
        self.public_key_to_connection_id = {}
        self.connection_id_to_public_key = {}
        self.connection_id_to_start_message: dict[
            str, agent.EdgeAgentToRelayStartMessage
        ] = {}

    async def handle_custom_agent_message(self, message: agent.AgentToRelayMessage):
        raise NotImplementedError()

    async def get_msg_loop_permission_and_create_connection_id(
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
        (
            msg_loop,
            connection_id,
        ) = await super().accept_ws_and_start_msg_loop_for_edge_agents(
            edge_agent_connection
        )
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
                "Cannot access agent %s with public key %s via ssh over websocket",
            )
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
            hardware_device = crud_hardware_device.create_or_update(
                db_session,
                self.connection_id_to_start_message[connection_id].hardware_ids,
                deployment_info.id,
            )

        async def msg_loop_but_close_connection_at_end():
            try:
                await msg_loop
            finally:
                # close the connection
                public_key = self.connection_id_to_public_key[connection_id]
                del self.public_key_to_connection_id[public_key]
                del self.connection_id_to_public_key[connection_id]
                del self.connection_id_to_start_message[connection_id]

        return msg_loop_but_close_connection_at_end(), connection_id
