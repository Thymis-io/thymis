import logging

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from thymis_controller import crud, models, project
from thymis_controller.config import global_settings
from thymis_controller.crud.task import get_tasks_short
from thymis_controller.nix import NIX_CMD, get_build_output
from thymis_controller.nix.log_parse import NixProcess
from thymis_controller.task.executor import TaskWorkerPoolManager
from thymis_controller.task.subscribe_ui import TaskUISubscriptionManager

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self):
        self.executor = TaskWorkerPoolManager()
        self.ui_subscription_manager = TaskUISubscriptionManager()

    async def start(self):
        await self.executor.start()
        await self.ui_subscription_manager.start()

    def get_tasks(self, session: Session):
        return get_tasks_short(session)

    async def subscribe_ui(self, websocket: WebSocket):
        await self.ui_subscription_manager.connect(websocket)
