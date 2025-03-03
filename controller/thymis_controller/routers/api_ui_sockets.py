import asyncio
import traceback
import uuid

import paramiko
from fastapi import APIRouter, WebSocket
from fastapi.concurrency import run_in_threadpool
from paramiko import PKey, SSHClient
from sqlalchemy.orm import Session
from thymis_controller import crud
from thymis_controller.config import global_settings
from thymis_controller.dependencies import (
    EngineAD,
    NetworkRelayAD,
    NotificationManagerAD,
    UserSessionIDAD,
)
from thymis_controller.tcp_to_ws import (
    channel_to_websocket,
    tcp_to_websocket,
    websocket_to_channel,
    websocket_to_tcp,
)

router = APIRouter()


@router.websocket("/notification")
async def notification_websocket(
    websocket: WebSocket,
    notification_manager: NotificationManagerAD,
    user_session_id: UserSessionIDAD,
):
    await notification_manager.connect(websocket, user_session_id)


@router.websocket("/vnc/{deployment_info_id}")
async def vnc_websocket(
    deployment_info_id: uuid.UUID,
    db_engine: EngineAD,
    websocket: WebSocket,
    network_relay: NetworkRelayAD,
):
    with Session(db_engine) as db_session:
        deployment_info = crud.deployment_info.get_by_id(db_session, deployment_info_id)

    if deployment_info is None:
        await websocket.close()
        return

    await websocket.accept()

    agent_connection_id = network_relay.public_key_to_connection_id.get(
        deployment_info.ssh_public_key
    )

    if agent_connection_id is None:
        await websocket.close()
        return

    try:
        connection = await network_relay.create_connection_async(
            agent_connection_id, "localhost", 5900, "tcp"
        )
    except Exception:
        await websocket.close()
        return

    tcp_to_ws_task = asyncio.create_task(tcp_to_websocket(connection, websocket))
    ws_to_tcp_task = asyncio.create_task(websocket_to_tcp(connection, websocket))

    try:
        await asyncio.gather(tcp_to_ws_task, ws_to_tcp_task)
    except Exception:
        traceback.print_exc()
    finally:
        tcp_to_ws_task.cancel()
        ws_to_tcp_task.cancel()


@router.websocket("/terminal/{deployment_info_id}")
async def terminal_websocket(
    deployment_info_id: uuid.UUID,
    websocket: WebSocket,
    db_engine: EngineAD,
    network_relay: NetworkRelayAD,
):
    with Session(db_engine) as db_session:
        deployment_info = crud.deployment_info.get_by_id(db_session, deployment_info_id)

    if deployment_info is None:
        await websocket.close()
        return

    await websocket.accept()

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
    client.set_missing_host_key_policy(
        CheckForExpectedHostKey(deployment_info.ssh_public_key)
    )

    pkey: PKey = PKey.from_path(global_settings.PROJECT_PATH / "id_thymis")

    agent_connection_id = network_relay.public_key_to_connection_id.get(
        deployment_info.ssh_public_key
    )

    if agent_connection_id is None:
        await websocket.close()
        return

    try:
        channel = await run_in_threadpool(
            connect_to_ssh_shell,
            client,
            None,
            None,
            await network_relay.create_connection(
                agent_connection_id, "localhost", 22, "tcp"
            ),
            pkey,
        )
    except ExpectedHostKeyNotFound:
        await websocket.send_bytes(b"Host key mismatch")
        await websocket.close()
        client.close()
        return
    except Exception as e:
        await websocket.send_bytes(str(e).encode())
        await websocket.close()
        client.close()
        return

    channel_to_ws_task = asyncio.create_task(channel_to_websocket(channel, websocket))
    ws_to_channel_task = asyncio.create_task(websocket_to_channel(channel, websocket))

    try:
        await asyncio.gather(channel_to_ws_task, ws_to_channel_task)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        channel_to_ws_task.cancel()
        ws_to_channel_task.cancel()
        client.close()


def connect_to_ssh_shell(
    client: SSHClient, tcp_ip: str | None, tcp_port: int | None, sock, pkey: PKey
):
    client.connect(
        hostname=tcp_ip or "localhost",
        port=tcp_port,
        sock=sock,
        username="root",
        pkey=pkey,
        timeout=30,
    )
    return client.invoke_shell()
