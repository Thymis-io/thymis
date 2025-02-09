import asyncio
import datetime
import threading
import traceback
import uuid
from queue import Queue
from typing import Literal, Union

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from pydantic import BaseModel, Field

NotificationDataInner = Union[
    "ShouldInvalidate", "FrontendToast", "ImageBuiltNotification"
]


class Notification:
    data: "NotificationData"
    creation_time: datetime.datetime
    last_try: datetime.datetime
    sent_to: list[WebSocket]

    def __init__(self, message: NotificationDataInner):
        self.data = NotificationData(inner=message)
        self.creation_time = datetime.datetime.now()
        self.last_try = datetime.datetime.max
        self.sent_to = []

    def recently_tried(self):
        now = datetime.datetime.now()
        return now - self.last_try < datetime.timedelta(seconds=1)

    def can_retry(self):
        now = datetime.datetime.now()
        return now - self.creation_time < datetime.timedelta(seconds=5)


class NotificationData(BaseModel):
    inner: NotificationDataInner = Field(discriminator="kind")


class ShouldInvalidate(BaseModel):
    kind: Literal["should_invalidate"] = "should_invalidate"
    should_invalidate_paths: list[str]


class FrontendToast(BaseModel):
    kind: Literal["frontend_toast"] = "frontend_toast"
    message: str


class ImageBuiltNotification(BaseModel):
    kind: Literal["image_built"] = "image_built"
    user_session_id: uuid.UUID
    configuration_id: str
    image_format: str


class NotificationManager:
    queue: Queue[Notification] = Queue()
    retry_queue: Queue[Notification] = Queue()
    alive: bool

    def __init__(self):
        self.active_connections: list[
            (WebSocket, uuid.UUID)
        ] = []  # connection, user_session_id

    def start(self):
        self.alive = True
        threading.Thread(target=self.start_send_queue).start()

    def stop(self):
        self.alive = False

    def start_send_queue(self):
        asyncio.run(self.send_queue())

    def next_notification(self) -> Notification | None:
        if self.queue.qsize() > 0:
            return self.queue.get()
        if self.retry_queue.qsize() > 0:
            notification = self.retry_queue.get()

            if notification.can_retry():
                return notification
        return None

    async def send_queue(self):
        while self.alive:
            notification = self.next_notification()

            if not notification:
                await asyncio.sleep(0.5)
                continue

            if notification.recently_tried():
                await asyncio.sleep(0.5)

            await self._broadcast(notification)
            notification.last_try = datetime.datetime.now()

            if notification.can_retry():
                self.retry_queue.put(notification)

    async def connect(self, websocket: WebSocket, user_session_id: uuid.UUID):
        await websocket.accept()

        try:
            while self.is_connection_healthy(websocket):
                await websocket.receive_bytes()
        except WebSocketDisconnect:
            pass
        finally:
            self.disconnect(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(
            next(
                (x for x in self.active_connections if x[0] == websocket),
                None,
            )
        )

    def is_connection_healthy(self, websocket: WebSocket):
        return WebSocketState.DISCONNECTED not in (
            websocket.application_state,
            websocket.client_state,
        )

    def broadcast_toast_notification(self, message: str):
        self.queue.put(Notification(FrontendToast(message=message)))

    async def _broadcast(self, message: Notification):
        for connection, user_session_id in self.active_connections:
            if (
                hasattr(message.data.inner, "user_session_id")
                and message.data.inner.user_session_id != user_session_id
            ):
                continue
            if connection in message.sent_to:
                continue
            if not self.is_connection_healthy(connection):
                continue
            try:
                await connection.send_text(message.data.model_dump_json())
                message.sent_to.append(connection)
            except Exception:
                self.disconnect(connection)
                traceback.print_exc()

    def broadcast_invalidate_notification(self, paths: list[str]):
        self.queue.put(Notification(ShouldInvalidate(should_invalidate_paths=paths)))

    def broadcast_image_built_notification(
        self, user_session_id: uuid.UUID, configuration_id: str, image_format: str
    ):
        self.queue.put(
            Notification(
                ImageBuiltNotification(
                    user_session_id=user_session_id,
                    configuration_id=configuration_id,
                    image_format=image_format,
                )
            )
        )
