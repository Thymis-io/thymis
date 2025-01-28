import logging

import http_network_relay
import http_network_relay.network_relay as nr
import thymis_agent.agent as agent
import thymis_controller.network_relay as nr
from fastapi import APIRouter, HTTPException, Request, WebSocket
from pydantic import BaseModel
from thymis_controller import crud, models
from thymis_controller.config import global_settings
from thymis_controller.dependencies import NetworkRelayAD, ProjectAD, SessionAD
from thymis_controller.nix import check_device_reference
from thymis_controller.utils import determine_first_host_with_key

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


# class NetworkRelay(nr.NetworkRelay):
#     CustomAgentToRelayMessage = agent.AgentToRelayMessage
#     CustomAgentToRelayStartMessage = agent.EdgeAgentToRelayStartMessage

#     def __init__(self):
#         super().__init__()

#     async def handle_custom_agent_message(self, message: agent.AgentToRelayMessage):
#         raise NotImplementedError()

#     async def check_agent_start_message_auth(
#         self, start_message: agent.EdgeAgentToRelayStartMessage, edge_agent_connection: WebSocket
#     ):
#         raise NotImplementedError()

#     async def get_agent_connection_id_from_start_message(
#         self, start_message: agent.EdgeAgentToRelayStartMessage, edge_agent_connection: WebSocket
#     ):
#         raise NotImplementedError()

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register")
def device_register(request: Request):
    logger.warning(f"{request.client.host} calls deprecated /agent/register endpoint")
    raise HTTPException(
        status_code=404, detail="The /agent/register endpoint is deprecated"
    )


@router.post("/heartbeat")
def device_heartbeat(request: Request):
    logger.warning(f"{request.client.host} calls deprecated /agent/heartbeat endpoint")
    raise HTTPException(
        status_code=404, detail="The /agent/heartbeat endpoint is deprecated"
    )


@router.post("/notify")
def device_notify(request: Request):
    logger.warning(f"{request.client.host} calls deprecated /agent/notify endpoint")
    raise HTTPException(
        status_code=404, detail="The /agent/notify endpoint is deprecated"
    )


@router.websocket("/relay")
async def websocket_endpoint(
    websocket: WebSocket,
    network_relay: NetworkRelayAD,
    project: ProjectAD,
    db_session: SessionAD,
):
    logger.info(f"Agent connection from {websocket.client.host}")
    res = await network_relay.accept_ws_and_start_msg_loop_for_edge_agents(websocket)
    if res is None:
        logger.error(f"Agent connection from {websocket.client.host} failed")
        return
    msg_loop, connection_id = res
    project.update_known_hosts(db_session)
    logger.info(
        f"Agent connection from {websocket.client.host} established with connection id {connection_id}"
    )
    await msg_loop
