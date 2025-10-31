import logging
from typing import Annotated, List

from fastapi import APIRouter, Header, HTTPException, Request, WebSocket
from pydantic import TypeAdapter
from sqlalchemy.orm import Session
from starlette.requests import ClientDisconnect
from thymis_controller import crud, models
from thymis_controller.crud.agent_token import check_token_validity
from thymis_controller.dependencies import (
    DBSessionAD,
    EngineAD,
    NetworkRelayAD,
    ProjectAD,
)

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


@router.post("/logs")
async def logs(
    request: Request,
    network_relay: NetworkRelayAD,
    project: ProjectAD,
    db_session: DBSessionAD,
    x_thymis_ssh_pubkey: Annotated[str | None, Header()] = None,
    x_thymis_token: Annotated[str | None, Header()] = None,
):
    # if token is invalid, reject
    if x_thymis_ssh_pubkey is None:
        logger.warning(f"No SSH public key from {request.client.host}")
        raise HTTPException(status_code=404)  # don't leak information
    if x_thymis_token is None:
        logger.warning(f"No token from {request.client.host}")
        raise HTTPException(status_code=404)
    # check if token is valid
    if not check_token_validity(db_session, x_thymis_token):
        logger.warning(f"Invalid token from {request.client.host}: {x_thymis_token}")
        raise HTTPException(status_code=404)
    # token is valid
    try:
        data = await request.body()
    except ClientDisconnect as e:
        logger.warning(
            f"Client disconnected before sending logs: {request.client.host}"
        )
        raise HTTPException(status_code=408) from e
    # parse as json
    ta = TypeAdapter(List[models.LogEntry])
    log_entries = ta.validate_json(data)
    for log_entry in log_entries:
        crud.logs.create(
            db_session,
            log_id=log_entry.uuid,
            timestamp=log_entry.timestamp,
            message=log_entry.message,
            hostname=log_entry.host,
            facility=log_entry.facility,
            severity=log_entry.severity,
            programname=log_entry.programname,
            syslogtag=log_entry.syslogtag,
            ssh_public_key=x_thymis_ssh_pubkey,
        )
