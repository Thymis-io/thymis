import asyncio
import logging

from fastapi import WebSocket
from thymis_controller import crud, db_models

logger = logging.getLogger(__name__)


class TaskUISubscriptionManager:
    # manages websocket subscriptions
    def __init__(self):
        self.subscribers: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.subscribers.add(websocket)
        try:
            while True:
                await websocket.receive_text()
        except:
            self.subscribers.remove(websocket)
        logger.info("Websocket disconnected")

    async def start(self):
        pass

    def stop(self):
        pass

    def notify_new_task(self, task: db_models.Task):
        short_task = crud.task.TaskShort.from_orm_task(task)
        for subscriber in self.subscribers:
            # TODO remove event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                subscriber.send_json(
                    {"type": "new_task", "task": short_task.model_dump(mode="json")}
                )
            )
            loop.close()

    def notify_task_update(self, task: db_models.Task):
        short_task = crud.task.TaskShort.from_orm_task(task)
        for subscriber in self.subscribers:
            # TODO remove event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                subscriber.send_json(
                    {"type": "task_update", "task": short_task.model_dump(mode="json")}
                )
            )
            loop.close()
