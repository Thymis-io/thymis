import contextlib
import logging
import os
from datetime import datetime

import sqlalchemy
from fastapi import WebSocket
from sqlalchemy.orm import Session
from thymis_controller import crud, db_models, models
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
        await self.ui_subscription_manager.start()
        await self.executor.start(db_engine)
        yield self
        self.executor.stop()
        self.ui_subscription_manager.stop()

    def get_tasks(self, session: Session, limit: int = 100, offset: int = 0):
        return get_tasks_short(session, limit, offset)

    def get_task_count(self, session: Session):
        return crud.task.get_task_count(session)

    async def subscribe_ui(self, websocket: WebSocket):
        await self.ui_subscription_manager.connect(websocket)

    def submit(self, task: TaskSubmissionData, db_session: Session) -> models.Task:
        # creates a database entry, then submits to executor
        task_db = task_create(
            db_session,
            start_time=datetime.now(),
            state="pending",
            task_type=task.type,
            task_submission_data=task.model_dump(mode="json"),
            parent_task_id=(
                task.parent_task_id if hasattr(task, "parent_task_id") else None
            ),
        )

        subtasks: list[db_models.Task] = []

        if task.type == "deploy_devices_task":
            children_uids = []
            for device in task.devices:
                submission_data = DeployDeviceTaskSubmission(
                    device=device,
                    project_path=task.project_path,
                    known_hosts_path=task.known_hosts_path,
                    ssh_key_path=task.ssh_key_path,
                    controller_ssh_pubkey=task.controller_ssh_pubkey,
                    parent_task_id=task_db.id,
                )
                subtask = task_create(
                    db_session,
                    start_time=datetime.now(),
                    state="pending",
                    task_type="deploy_device_task",
                    task_submission_data=submission_data.model_dump(mode="json"),
                    parent_task_id=task_db.id,
                )
                children_uids.append(str(subtask.id))
                subtasks.append(subtask)
            task_db.children = children_uids
            db_session.commit()

        self.executor.submit(TaskSubmission(id=task_db.id, data=task))

        for subtask in subtasks:
            self.executor.submit(
                TaskSubmission(id=subtask.id, data=subtask.task_submission_data)
            )

        return task_db

    def get_task(self, task_id: str, db_session: Session) -> models.Task:
        return models.task.Task.model_validate(
            crud.task.get_task_by_id(db_session, task_id),
            from_attributes=True,
        )

    def cancel_task(self, task_id: str):
        self.executor.cancel_task(task_id)

    def retry_task(self, task_id: str, db_session: Session):
        task = crud.task.get_task_by_id(db_session, task_id)
        task_data = TaskSubmission.from_orm_task(task).data
        self.submit(task_data, db_session)

    def delete_all_tasks(self, db_session: Session):
        if "RUNNING_IN_PLAYWRIGHT" in os.environ:
            for task in crud.task.get_pending_tasks(db_session):
                task.state = "failed"
                task.add_exception("Task was running when controller was shut down")
            self.executor.cancel_all_tasks()
            db_session.commit()
            crud.task.delete_all_tasks(db_session)
