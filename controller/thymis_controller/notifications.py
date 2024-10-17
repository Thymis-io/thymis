from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState


class NotificationManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        try:
            while True:
                await websocket.receive_bytes()
        except WebSocketDisconnect:
            await self.disconnect(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json({"message": message})

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            if (
                connection.application_state == WebSocketState.DISCONNECTED
                or connection.client_state == WebSocketState.DISCONNECTED
            ):
                continue
            try:
                await connection.send_json({"message": message})
            except Exception as e:
                print(e)
                self.active_connections.remove(connection)


notification_manager = NotificationManager()
