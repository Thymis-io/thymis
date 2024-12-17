import contextlib
import logging
from datetime import datetime

import sqlalchemy
from fastapi import WebSocket
from sqlalchemy.orm import Session
from thymis_controller import crud, models
from thymis_controller.crud.task import create as task_create
from thymis_controller.crud.task import get_tasks_short
from thymis_controller.models.task import (
    DeployDeviceTaskSubmission,
    TaskSubmission,
    TaskSubmissionData,
)
from thymis_controller.task.executor import TaskWorkerPoolManager
from thymis_controller.task.subscribe_ui import TaskUISubscriptionManager

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self):
        self.executor = TaskWorkerPoolManager()
        self.ui_subscription_manager = TaskUISubscriptionManager()
        self.executor.subscribe_ui(self.ui_subscription_manager)

    @contextlib.asynccontextmanager
    async def start(self, db_engine: sqlalchemy.Engine):
        await self.executor.start(db_engine)
        await self.ui_subscription_manager.start()
        yield self
        self.executor.stop()
        self.ui_subscription_manager.stop()

    def get_tasks(self, session: Session):
        return get_tasks_short(session)

    async def subscribe_ui(self, websocket: WebSocket):
        await self.ui_subscription_manager.connect(websocket)

    def submit(self, task: TaskSubmissionData, db_session: Session) -> models.Task:
        # creates a database entry, then submits to executor
        task_db = task_create(
            db_session,
            start_time=datetime.now(),
            state="pending",
            task_type=task.type,
            task_submission_data=task.model_dump(),
            parent_task_id=(
                task.parent_task_id if hasattr(task, "parent_task_id") else None
            ),
        )

        self.executor.submit(TaskSubmission(id=task_db.id, data=task))

        if task.type == "deploy_devices_task":
            children_uids = []
            for device in task.devices:
                submission_data = DeployDeviceTaskSubmission(
                    device=device,
                    known_hosts_path=task.known_hosts_path,
                    ssh_key_path=task.ssh_key_path,
                    parent_task_id=task_db.id,
                )
                subtask = self.submit(submission_data, db_session)
                children_uids.append(subtask.id)
            task_db.children = children_uids
            db_session.commit()

        return task_db

    def get_task(self, task_id: str, db_session: Session) -> models.Task:
        return models.task.Task.model_validate(
            crud.task.get_task_by_id(db_session, task_id),
            from_attributes=True,
        )
