import logging

import http_network_relay
import http_network_relay.network_relay as nr
import thymis_agent.agent as agent
import thymis_controller.network_relay as nr
from fastapi import APIRouter, HTTPException, Request, WebSocket
from pydantic import BaseModel
from sqlalchemy.orm import Session
from thymis_controller import crud, models
from thymis_controller.config import global_settings
from thymis_controller.dependencies import EngineAD, NetworkRelayAD, ProjectAD
from thymis_controller.nix import check_device_reference
from thymis_controller.utils import determine_first_host_with_key

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
async def relay(
    websocket: WebSocket,
    network_relay: NetworkRelayAD,
    project: ProjectAD,
    db_engine: EngineAD,
):
    logger.info(f"Agent connection from {websocket.client.host}")
    res = await network_relay.accept_ws_and_start_msg_loop_for_edge_agents(websocket)
    if res is None:
        logger.error(f"Agent connection from {websocket.client.host} failed")
        return
    msg_loop, connection_id = res
    with Session(db_engine) as db_session:
        project.update_known_hosts(db_session)
    logger.info(
        f"Agent connection from {websocket.client.host} established with connection id {connection_id}"
    )
    await msg_loop


@router.websocket("/relay_for_clients")
async def relay_for_clients(
    websocket: WebSocket,
    network_relay: NetworkRelayAD,
):
    logger.info(f"Agent connection from {websocket.client.host}")
    await network_relay.ws_for_access_clients(websocket)
