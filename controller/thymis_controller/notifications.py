import asyncio
import threading
import traceback

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState


class NotificationManager:
    queued_messages: list[str] = []

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        for message in self.queued_messages:
            await self.broadcast(message, False)
        self.queued_messages = []

        try:
            while self.is_connection_healthy(websocket):
                await websocket.receive_bytes()
        except WebSocketDisconnect:
            self.disconnect(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    def is_connection_healthy(self, websocket: WebSocket):
        return (
            websocket.application_state != WebSocketState.DISCONNECTED
            and websocket.client_state != WebSocketState.DISCONNECTED
        )

    def send_personal_message(self, message: str, websocket: WebSocket):
        threading.Thread(
            target=lambda: self.run_async_in_thread(
                self._send_personal_message, message, websocket
            )
        ).start()

    async def _send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json({"message": message})

    def broadcast(self, message: str, queue_if_unsent: bool = True):
        self.run_async_in_thread(self._broadcast, message, queue_if_unsent)

    @staticmethod
    def run_async_in_thread(async_func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.create_task(async_func(*args, **kwargs))

    async def _broadcast(self, message: str, queue_if_unsent: bool = True):
        message_sent = False
        for connection in self.active_connections:
            if not self.is_connection_healthy(connection):
                continue
            try:
                await connection.send_json({"message": message})
                message_sent = True
            except Exception:
                self.active_connections.remove(connection)
                traceback.print_exc()

        if queue_if_unsent and not message_sent:
            self.queued_messages.append(message)

            if len(self.queued_messages) > 10:
                self.queued_messages = self.queued_messages[-10:]


notification_manager = NotificationManager()
