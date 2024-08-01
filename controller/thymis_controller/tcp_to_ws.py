import asyncio

from fastapi import WebSocket, WebSocketDisconnect


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
