import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect
from paramiko import Channel


async def tcp_to_websocket(tcp_reader, websocket):
    try:
        while True:
            data = await tcp_reader.read(1024)
            if not data:
                break
            await websocket.send_bytes(data)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error in tcp_to_websocket: {e}")
    finally:
        await websocket.close()


async def websocket_to_tcp(tcp_writer, websocket):
    try:
        while True:
            data = await websocket.receive_bytes()
            tcp_writer.write(data)
            await tcp_writer.drain()
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error in websocket_to_tcp: {e}")
    finally:
        tcp_writer.close()


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
    except Exception as e:
        print(f"Error in channel_to_websocket: {e}")
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
    except Exception as e:
        print(f"Error in websocket_to_channel: {e}")
    finally:
        channel.close()
