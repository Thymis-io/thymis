import asyncio
import contextlib
import logging
import os
import random
import threading
import time
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy
from fastapi import WebSocket
from sqlalchemy.orm import Session
from thymis_controller import crud, db_models, models
from thymis_controller.crud.agent_token import create_access_client_token
from thymis_controller.crud.task import create as task_create
from thymis_controller.crud.task import get_tasks_short
from thymis_controller.models.task import (
    DeployDeviceTaskSubmission,
    TaskSubmission,
    TaskSubmissionData,
)
from thymis_controller.task.executor import TaskWorkerPoolManager
from thymis_controller.task.subscribe_ui import TaskUISubscriptionManager

if TYPE_CHECKING:
    from thymis_controller.network_relay import NetworkRelay

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self, access_client_endpoint: str, network_relay: "NetworkRelay"):
        self.executor = TaskWorkerPoolManager(self)
        self.ui_subscription_manager = TaskUISubscriptionManager(self)
        self.access_client_endpoint = access_client_endpoint
        self.network_relay = network_relay
        network_relay.task_controller = self
        self.loop = None

    @contextlib.asynccontextmanager
    async def start(self, db_engine: sqlalchemy.Engine):
        self.loop = asyncio.get_event_loop()
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
                access_client_token = random.randbytes(32).hex()
                submission_data = DeployDeviceTaskSubmission(
                    device=device,
                    project_path=task.project_path,
                    known_hosts_path=task.known_hosts_path,
                    ssh_key_path=task.ssh_key_path,
                    controller_access_client_endpoint=self.access_client_endpoint,
                    controller_ssh_pubkey=task.controller_ssh_pubkey,
                    parent_task_id=task_db.id,
                    access_client_token=access_client_token,
                )
                subtask = task_create(
                    db_session,
                    start_time=datetime.now(),
                    state="pending",
                    task_type="deploy_device_task",
                    task_submission_data=submission_data.model_dump(mode="json"),
                    parent_task_id=task_db.id,
                )
                access_client_token_db = create_access_client_token(
                    db_session,
                    deployment_info_id=device.deployment_info_id,
                    token=access_client_token,
                    deploy_device_task_id=subtask.id,
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
        return models.task.Task.from_orm_task(
            crud.task.get_task_by_id(db_session, task_id),
        )

    def cancel_task(self, task_id: str):
        self.executor.cancel_task(task_id)

    def retry_task(self, task_id: str, db_session: Session):
        task = crud.task.get_task_by_id(db_session, task_id)
        task_data = TaskSubmission.from_orm_task(task).data
        self.submit(task_data, db_session)

    def delete_all_tasks(self, db_session: Session):
        if "RUNNING_IN_PLAYWRIGHT" in os.environ:
            task_ids = []
            for task in crud.task.get_all_tasks(db_session):
                # save their ids
                task_ids.append(task.id)
            # while there are still alive tasks, spam cancel them
            start_time = time.time()
            while (
                crud.task.get_all_alive_tasks(db_session)
                and any(future.running() for future in self.executor.futures)
                and time.time() - start_time < 6
            ):
                for task_id in task_ids:
                    self.executor.cancel_task(task_id)
                time.sleep(0.1)
            # switch to a new executor
            db_engine = self.executor._db_engine
            # self.executor.stop()
            threading.Thread(target=self.executor.stop).start()
            self.executor = TaskWorkerPoolManager(self)
            asyncio.run_coroutine_threadsafe(self.executor.start(db_engine), self.loop)
            crud.task.delete_all_tasks(db_session)
