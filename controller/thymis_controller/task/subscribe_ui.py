import asyncio
import asyncio.queues
import logging
import threading
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
    task: models.Task


class TaskWebsocketSubscriber:
    def __init__(
        self, db_engine: Engine, controller: TaskController, websocket: WebSocket
    ):
        self.loop = asyncio.get_event_loop()
        self.task_queue = asyncio.Queue[TaskMessage]()
        self.send_lock = asyncio.Lock()
        self.process_subscribed_task_lock = threading.Lock()
        self.db_engine = db_engine
        self.controller = controller
        self.websocket = websocket
        with self.process_subscribed_task_lock:
            self.reset_subscribed_task(None)

    def reset_subscribed_task(self, task_id: uuid.UUID | None):
        self.subscribed_task = task_id
        self.stdout_count = 0
        self.stderr_count = 0
        self.nix_errors_count = 0
        self.nix_error_logs_count = 0
        self.nix_warning_logs_count = 0
        self.nix_notice_logs_count = 0
        self.nix_info_logs_count = 0

    def connect(self):
        self.controller.executor.on_new_task.subscribe(self.notify_new_task)
        self.controller.executor.on_task_update.subscribe(self.notify_task_update)
        self.controller.executor.on_task_output.subscribe(self.notify_task_output)

    def disconnect(self):
        self.controller.executor.on_new_task.unsubscribe(self.notify_new_task)
        self.controller.executor.on_task_update.unsubscribe(self.notify_task_update)
        self.controller.executor.on_task_output.unsubscribe(self.notify_task_output)

    async def run(self):
        send_task = self.loop.create_task(self.send_loop())
        receive_task = self.loop.create_task(self.receive_loop())

        try:
            await asyncio.gather(send_task, receive_task)
        except (WebSocketDisconnect, asyncio.QueueShutDown, asyncio.CancelledError):
            return
        except Exception:
            return
        finally:
            send_task.cancel()
            receive_task.cancel()

    async def send_loop(self):
        while True:
            task = await self.task_queue.get()
            async with self.send_lock:
                if (
                    task.type == "subscribed_task"
                    and self.subscribed_task != task.task_id
                ):
                    return
                await self.websocket.send_json(task.model_dump(mode="json"))

    async def receive_loop(self):
        while True:
            message = await self.websocket.receive_json()
            if "type" in message and message["type"] == "subscribe_task":
                task_id = uuid.UUID(message["task_id"])
                async with self.send_lock:
                    with self.process_subscribed_task_lock:
                        self.reset_subscribed_task(task_id)
                        with Session(self.db_engine) as db_session:
                            task = self.controller.get_task(task_id, db_session)
                        subscribed_task = self.create_subscribed_task(task)
                    await self.websocket.send_json(
                        SubscribedTask(
                            task_id=task_id, task=subscribed_task
                        ).model_dump(mode="json")
                    )

    def create_subscribed_task(self, db_task: db_models.Task):
        # pylint: disable=attribute-defined-outside-init
        task = models.Task.from_orm_task(db_task)
        if task.process_stdout:
            task.process_stdout = task.process_stdout[self.stdout_count :]
            self.stdout_count = len(db_task.process_stdout)
        if task.process_stderr:
            task.process_stderr = task.process_stderr[self.stderr_count :]
            self.stderr_count = len(db_task.process_stderr)
        if task.nix_errors:
            task.nix_errors = task.nix_errors[self.nix_errors_count :]
            self.nix_errors_count = len(db_task.nix_errors)
        if task.nix_error_logs:
            task.nix_error_logs = task.nix_error_logs[self.nix_error_logs_count :]
            self.nix_error_logs_count = len(db_task.nix_error_logs)
        if task.nix_warning_logs:
            task.nix_warning_logs = task.nix_warning_logs[self.nix_warning_logs_count :]
            self.nix_warning_logs_count = len(db_task.nix_warning_logs)
        if task.nix_notice_logs:
            task.nix_notice_logs = task.nix_notice_logs[self.nix_notice_logs_count :]
            self.nix_notice_logs_count = len(db_task.nix_notice_logs)
        if task.nix_info_logs:
            task.nix_info_logs = task.nix_info_logs[self.nix_info_logs_count :]
            self.nix_info_logs_count = len(db_task.nix_info_logs)
        return task

    def enqueue_task(self, task_message: TaskMessage):
        self.loop.call_soon_threadsafe(self.task_queue.put_nowait, task_message)

    def notify_new_task(self, task: db_models.Task):
        short_task = crud.task.TaskShort.from_orm_task(task)
        self.enqueue_task(NewShortTask(task_id=task.id, task=short_task))

    def notify_task_update(self, task: db_models.Task):
        short_task = crud.task.TaskShort.from_orm_task(task)
        self.enqueue_task(ShortTaskUpdate(task_id=task.id, task=short_task))

    def notify_task_output(self, task: db_models.Task):
        with self.process_subscribed_task_lock:
            if self.subscribed_task == task.id:
                self.enqueue_task(
                    SubscribedTaskOutput(
                        task_id=task.id, task=self.create_subscribed_task(task)
                    )
                )
