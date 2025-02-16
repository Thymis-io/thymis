import asyncio
import asyncio.queues
import logging
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from thymis_controller import crud, db_models, models
from thymis_controller.task.controller import TaskController

logger = logging.getLogger(__name__)


class TaskMessage(BaseModel):
    type: str
    task_id: uuid.UUID


class NewShortTask(TaskMessage):
    type: str = "new_short_task"
    task: models.TaskShort


class ShortTaskUpdate(TaskMessage):
    type: str = "short_task_update"
    task: models.TaskShort


class SubscribedTask(TaskMessage):
    type: str = "subscribed_task"
    task: models.Task


class SubscribedTaskOutput(TaskMessage):
    type: str = "subscribed_task_output"
    stdout: str
    stderr: str


class TaskWebsocketSubscriber:
    def __init__(self, db_engine: Engine, controller: TaskController):
        self.loop = asyncio.get_event_loop()
        self.task_queue = asyncio.Queue[TaskMessage]()
        self.send_lock = asyncio.Lock()
        self.websocket: WebSocket | None = None
        self.subscribed_task: uuid.UUID | None = None
        self.db_engine = db_engine
        self.controller = controller

    async def connect(self, websocket: WebSocket):
        self.websocket = websocket
        self.controller.executor.on_new_task.subscribe(self.notify_new_task)
        self.controller.executor.on_task_update.subscribe(self.notify_task_update)
        self.controller.executor.on_task_output.subscribe(self.notify_task_output)

        send_task_coroutine = self.loop.create_task(self.websocket_loop(self.send_task))
        receive_task_coroutine = self.loop.create_task(
            self.websocket_loop(self.receive_message)
        )
        await asyncio.gather(send_task_coroutine, receive_task_coroutine)

    async def websocket_loop(self, inner):
        while True:
            try:
                await inner()
            except (WebSocketDisconnect, asyncio.QueueShutDown):
                break
            except Exception as e:
                logger.warning(f"Unexpected Exception in websocket_loop: {type(e)}")
                break

    async def send_task(self):
        task = await self.task_queue.get()
        async with self.send_lock:
            if task.type == "subscribed_task" and self.subscribed_task != task.task_id:
                return
            await self.websocket.send_json(task.model_dump(mode="json"))

    async def receive_message(self):
        message = await self.websocket.receive_json()
        if "type" in message and message["type"] == "subscribe_task":
            task_id = uuid.UUID(message["task_id"])
            async with self.send_lock:
                self.subscribed_task = task_id
                with Session(self.db_engine) as db_session:
                    task = self.controller.get_task(task_id, db_session)
                await self.websocket.send_json(
                    SubscribedTask(task_id=task_id, task=task).model_dump(mode="json")
                )

    def enqueue_task(self, task_message: TaskMessage):
        self.loop.call_soon_threadsafe(self.task_queue.put_nowait, task_message)

    def notify_new_task(self, task: db_models.Task):
        short_task = crud.task.TaskShort.from_orm_task(task)
        self.enqueue_task(NewShortTask(task_id=task.id, task=short_task))

    def notify_task_update(self, task: db_models.Task):
        short_task = crud.task.TaskShort.from_orm_task(task)
        self.enqueue_task(ShortTaskUpdate(task_id=task.id, task=short_task))

    def notify_task_output(self, task: db_models.Task, stdout: str, stderr: str):
        if self.subscribed_task == task.id:
            self.enqueue_task(
                SubscribedTaskOutput(task_id=task.id, stdout=stdout, stderr=stderr)
            )
