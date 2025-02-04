import asyncio
import json
import traceback

from fastapi import WebSocket, WebSocketDisconnect
from http_network_relay.network_relay import TcpConnectionAsync
from paramiko import Channel


async def tcp_to_websocket(connection: TcpConnectionAsync, websocket: WebSocket):
    try:
        while True:
            data = await connection.read(1024)
            if not data:
                break
            await websocket.send_bytes(data)
    except asyncio.CancelledError:
        pass
    except Exception:
        traceback.print_exc()
    finally:
        await websocket.close()


async def websocket_to_tcp(connection: TcpConnectionAsync, websocket: WebSocket):
    try:
        while True:
            data = await websocket.receive_bytes()
            await connection.send(data)
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    except Exception:
        traceback.print_exc()
    finally:
        await connection.close()


async def channel_to_websocket(channel: Channel, websocket: WebSocket):
    try:
        while True:
            if channel.closed:
                break
            if not channel.recv_ready():
                await asyncio.sleep(0.01)
                continue
            data = channel.recv(1024)
            if not data:
                break
            await websocket.send_bytes(data)
    except asyncio.CancelledError:
        pass
    except Exception:
        traceback.print_exc()
    finally:
        await websocket.close()


async def websocket_to_channel(channel: Channel, websocket: WebSocket):
    try:
        while True:
            data = await websocket.receive_text()
            if not data:
                break
            if data.startswith("\x04"):
                data = data[1:]
                data = json.loads(data)
                channel.resize_pty(width=data["cols"], height=data["rows"])
            else:
                channel.send(data.encode())
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    except Exception:
        traceback.print_exc()
    finally:
        channel.close()
