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
from thymis_controller import models

NotificationDataInner = Union[
    "ShouldInvalidate",
    "FrontendToast",
    "ImageBuiltNotification",
    "DeploymentInfoUpdateNotification",
]

INVALIDATE_DEBOUNCE_SECONDS: float = 0.2


class Notification:
    data: "NotificationData"
    creation_time: datetime.datetime
    sent_to: list[WebSocket]

    def __init__(self, message: NotificationDataInner):
        self.data = NotificationData(inner=message)
        self.creation_time = datetime.datetime.now()
        self.sent_to = []


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


class DeploymentInfoUpdateNotification(BaseModel):
    kind: Literal["deployment_info_update"] = "deployment_info_update"
    deployment_infos: list["models.DeploymentInfo"]


class NotificationManager:
    queue: "Queue[Notification]"
    alive: bool

    def __init__(self):
        self.queue: Queue[Notification] = Queue()
        self.active_connections: dict[WebSocket, uuid.UUID] = {}
        self.loop: asyncio.AbstractEventLoop = None
        self.invalidate_paths_lock = threading.Lock()
        self.pending_invalidate_paths: set[str] = set()
        self.invalidate_timer: threading.Timer | None = None

    def start(self):
        self.alive = True
        self.loop = asyncio.get_event_loop()  # called from uvicorn/asyncio thread
        threading.Thread(target=self.start_send_queue, daemon=True).start()

    def stop(self):
        self.alive = False
        # unblock queue.get() so the background thread can exit
        self.queue.put(Notification(ShouldInvalidate(should_invalidate_paths=[])))

    def start_send_queue(self):
        # blocking loop — runs in background thread, uses queue.get() to block
        while self.alive:
            notification = self.queue.get()
            if not self.alive:  # sentinel check after wake-up from stop()
                break
            future = asyncio.run_coroutine_threadsafe(
                self._broadcast(notification), self.loop
            )
            try:
                future.result()
            except Exception:
                traceback.print_exc()

    async def connect(self, websocket: WebSocket, user_session_id: uuid.UUID):
        await websocket.accept()
        self.active_connections[websocket] = user_session_id

        try:
            while self.is_connection_healthy(websocket):
                await websocket.receive_bytes()
        except WebSocketDisconnect:
            pass
        finally:
            self.disconnect(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)

    def is_connection_healthy(self, websocket: WebSocket):
        return WebSocketState.DISCONNECTED not in (
            websocket.application_state,
            websocket.client_state,
        )

    def broadcast_toast_notification(self, message: str):
        self.queue.put(Notification(FrontendToast(message=message)))

    async def _broadcast(self, message: Notification):
        for connection, user_session_id in list(self.active_connections.items()):
            if (
                hasattr(message.data.inner, "user_session_id")
                and message.data.inner.user_session_id != user_session_id
            ):
                continue
            if connection in message.sent_to:
                continue
            if not self.is_connection_healthy(connection):
                self.disconnect(connection)
                continue
            try:
                await connection.send_text(message.data.model_dump_json())
                message.sent_to.append(connection)
            except Exception:
                self.disconnect(connection)
                traceback.print_exc()

    def broadcast_invalidate_notification(self, paths: list[str]):
        with self.invalidate_paths_lock:
            self.pending_invalidate_paths.update(paths)
            if self.invalidate_timer is None:
                self.invalidate_timer = threading.Timer(
                    INVALIDATE_DEBOUNCE_SECONDS, self._flush_invalidate
                )
                self.invalidate_timer.daemon = True
                self.invalidate_timer.start()

    def _flush_invalidate(self):
        with self.invalidate_paths_lock:
            paths = list(self.pending_invalidate_paths)
            self.pending_invalidate_paths.clear()
            self.invalidate_timer = None
        if paths:
            self.queue.put(
                Notification(ShouldInvalidate(should_invalidate_paths=paths))
            )

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

    def broadcast_deployment_info_update(
        self, deployment_infos: list[models.DeploymentInfo]
    ):
        self.queue.put(
            Notification(
                DeploymentInfoUpdateNotification(deployment_infos=deployment_infos)
            )
        )
