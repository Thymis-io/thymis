import logging
from typing import Annotated, List

from fastapi import APIRouter, Header, HTTPException, Request, WebSocket
from pydantic import TypeAdapter
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect
from thymis_controller import crud, models
from thymis_controller.crud import agent_token as agent_token_crud
from thymis_controller.crud.agent_token import check_token_validity
from thymis_controller.dependencies import (
    DBSessionAD,
    EngineAD,
    LogIngestorAD,
    NetworkRelayAD,
    ProjectAD,
)

logger = logging.getLogger(__name__)
ta = TypeAdapter(List[models.LogEntry])

router = APIRouter()


@router.post("/enroll")
def enroll(
    request: models.EnrollRequest, db_session: DBSessionAD, project: ProjectAD
) -> models.EnrollResponse:
    successor = crud.pairing_code.redeem(db_session, request.code, request.nonce)
    if successor is None:
        raise HTTPException(status_code=404)
    return models.EnrollResponse(
        token=successor.token, controller_ssh_pubkey=project.public_key
    )


@router.get("/controller-ssh-pubkey")
def controller_ssh_pubkey(
    request: Request,
    db_session: DBSessionAD,
    project: ProjectAD,
    x_thymis_token: Annotated[str | None, Header()] = None,
) -> models.ControllerPublicKeyResponse:
    if x_thymis_token is None or not check_token_validity(db_session, x_thymis_token):
        logger.warning(f"Invalid token from {request.client.host}")
        raise HTTPException(status_code=404)
    if not project.public_key:
        # Misconfigured controller: hand back nothing so the agent keeps whatever
        # key it already trusts instead of erroring out mid-boot.
        logger.error("Controller has no SSH public key to hand out")
    return models.ControllerPublicKeyResponse(controller_ssh_pubkey=project.public_key)


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
    db_session: DBSessionAD,
    log_ingestor: LogIngestorAD,
    x_thymis_ssh_pubkey: Annotated[str | None, Header()] = None,
    x_thymis_token: Annotated[str | None, Header()] = None,
):
    """Accept a batch of syslog entries from a device.

    The request only validates the payload and enqueues it: SQLite work happens
    in the LogIngestor's worker, merged with other pending batches. Ingest must
    not wait on a write lock or a large commit, or the device's rsyslog omhttp
    action times out and retries.
    """
    if x_thymis_ssh_pubkey is None:
        logger.warning(f"No SSH public key from {request.client.host}")
        raise HTTPException(status_code=404)  # don't leak information
    if x_thymis_token is None:
        logger.warning(f"No token from {request.client.host}")
        raise HTTPException(status_code=404)
    if not agent_token_crud.is_token_cached_valid(x_thymis_token):
        valid_token = await run_in_threadpool(
            check_token_validity, db_session, x_thymis_token
        )
        if not valid_token:
            logger.warning(f"Invalid token from {request.client.host}")
            raise HTTPException(status_code=404)
    try:
        data = await request.body()
    except ClientDisconnect as e:
        logger.warning(
            f"Client disconnected before sending logs: {request.client.host}"
        )
        raise HTTPException(status_code=408) from e
    # Devices post a few entries per request; parsing those on the loop is
    # cheaper than a thread handoff. Keep oversized payloads off the loop.
    if len(data) <= 256 * 1024:
        log_entries = ta.validate_json(data)
    else:
        log_entries = await run_in_threadpool(ta.validate_json, data)
    log_ingestor.submit(x_thymis_ssh_pubkey, log_entries)
