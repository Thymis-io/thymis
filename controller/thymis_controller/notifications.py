import traceback

from fastapi import BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState


class NotificationManager:
    queued_messages: list[str] = []

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        queued_messages = list(self.queued_messages)
        self.queued_messages = []
        for message in queued_messages:
            await self.broadcast(message)

        try:
            while websocket.application_state != WebSocketState.DISCONNECTED:
                await websocket.receive_bytes()
        except WebSocketDisconnect:
            self.disconnect(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json({"message": message})

    async def broadcast(self, message: str):
        send_anywhere = False
        for connection in self.active_connections:
            if (
                connection.application_state == WebSocketState.DISCONNECTED
                or connection.client_state == WebSocketState.DISCONNECTED
            ):
                continue
            try:
                await connection.send_json({"message": message})
                send_anywhere = True
            except Exception:
                self.active_connections.remove(connection)
                traceback.print_exc()
        if not send_anywhere:
            self.queued_messages.append(message)


notification_manager = NotificationManager()
