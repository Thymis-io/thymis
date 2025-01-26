import asyncio
import asyncio.queues
import logging
import threading

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from thymis_controller import crud, db_models

logger = logging.getLogger(__name__)


class TaskUISubscriptionManager:
    # manages websocket subscriptions
    def __init__(self):
        self.subscribers: set[WebSocket] = set()
        self.subscribers_lock = threading.Lock()
        self.task_queue = asyncio.Queue()
        self.send_thread: threading.Thread | None = None
        self.loop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self.subscribers_lock:
            self.subscribers.add(websocket)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            with self.subscribers_lock:
                self.subscribers.remove(websocket)
        logger.info("Websocket disconnected")

    async def start(self):
        asyncio.create_task(self.send_loop())

    def stop(self):
        self.loop.call_soon_threadsafe(self.task_queue.shutdown)

    async def send_loop(self):
        self.loop = asyncio.get_event_loop()
        while True:
            try:
                task = await self.task_queue.get()

                with self.subscribers_lock:
                    subscribers = self.subscribers.copy()

                for subscriber in subscribers:
                    if subscriber.application_state == WebSocketState.CONNECTED:
                        try:
                            await subscriber.send_json(task)
                        except WebSocketDisconnect:
                            with self.subscribers_lock:
                                self.subscribers.remove(subscriber)
            except asyncio.QueueShutDown:
                break

    def notify_new_task(self, task: db_models.Task):
        short_task = crud.task.TaskShort.from_orm_task(task)
        self.loop.call_soon_threadsafe(
            self.task_queue.put_nowait,
            {"type": "new_task", "task": short_task.model_dump(mode="json")},
        )

    def notify_task_update(self, task: db_models.Task):
        short_task = crud.task.TaskShort.from_orm_task(task)
        self.loop.call_soon_threadsafe(
            self.task_queue.put_nowait,
            {"type": "task_update", "task": short_task.model_dump(mode="json")},
        )
