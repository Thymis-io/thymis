import contextlib
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import sqlalchemy
from sqlalchemy.orm import Session
from thymis_controller import crud, db_models, models
from thymis_controller.crud.agent_token import get_or_create_access_client_token
from thymis_controller.crud.task import get_tasks_short
from thymis_controller.image_updates import next_update_version
from thymis_controller.models.task import (
    DeployDeviceTaskSubmission,
    TaskSubmission,
    TaskSubmissionData,
)
from thymis_controller.task.executor import TaskWorkerPoolManager

if TYPE_CHECKING:
    from thymis_controller.network_relay import NetworkRelay
    from thymis_controller.notifications import NotificationManager
    from thymis_controller.project import Project

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(
        self,
        access_client_endpoint: str,
        network_relay: "NetworkRelay",
        notification_manager: "NotificationManager",
        project: "Project",
    ):
        self.executor = TaskWorkerPoolManager(self)
        self.access_client_endpoint = access_client_endpoint
        self.network_relay = network_relay
        network_relay.task_controller = self
        self.notification_manager = notification_manager
        self.project = project
        self._submission_lock = threading.Lock()

    @contextlib.asynccontextmanager
    async def start(self, db_engine: sqlalchemy.Engine):
        await self.executor.start(db_engine)
        yield self
        self.executor.stop()

    def get_tasks(self, session: Session, limit: int = 100, offset: int = 0):
        return get_tasks_short(session, limit, offset)

    def get_task_count(self, session: Session):
        return crud.task.get_task_count(session)

    def submit(
        self, task: TaskSubmissionData, user_session_id: uuid.UUID, db_session: Session
    ) -> models.Task:
        with self._submission_lock:
            return self._submit_locked(task, user_session_id, db_session)

    def _submit_locked(
        self, task: TaskSubmissionData, user_session_id: uuid.UUID, db_session: Session
    ) -> models.Task:
        deployment_devices = (
            task.devices
            if task.type == "deploy_devices_task"
            else [task.device]
            if task.type == "deploy_device_task"
            else []
        )
        if any(
            device.target_uses_image_updates != (device.image_update_state is not None)
            for device in deployment_devices
        ):
            raise ValueError(
                "Changing between legacy and A/B system images requires "
                "re-provisioning the device"
            )
        image_devices = [
            device for device in deployment_devices if device.target_uses_image_updates
        ]
        deployment_info_ids = [device.deployment_info_id for device in image_devices]
        if len(set(deployment_info_ids)) != len(deployment_info_ids):
            raise ValueError("A device can only occur once in an image deployment")
        excluded_parent_task_id = (
            task.parent_task_id if hasattr(task, "parent_task_id") else None
        )
        for configuration_id in {device.identifier for device in image_devices}:
            if crud.task.has_alive_image_config_task(
                db_session,
                configuration_id,
                exclude_task_id=excluded_parent_task_id,
            ):
                raise ValueError(
                    "An image deployment is already publishing this configuration"
                )
        for deployment_info_id in deployment_info_ids:
            if crud.task.has_alive_deployment_task(
                db_session,
                deployment_info_id,
                exclude_task_id=excluded_parent_task_id,
            ):
                raise ValueError(
                    "An image deployment is already running for this device"
                )
            deployment_info = crud.deployment_info.get_by_id(
                db_session, deployment_info_id
            )
            if deployment_info.pending_image_task_id is not None:
                crud.deployment_info.update(
                    db_session,
                    deployment_info_id,
                    pending_image_version=None,
                    pending_image_task_id=None,
                    pending_image_config_id=None,
                    pending_image_config_commit=None,
                )

        if image_devices:
            timestamp_ms = time.time_ns() // 1_000_000
            image_version = str(timestamp_ms)
            for device in image_devices:
                if device.image_update_state is not None:
                    device_version = next_update_version(
                        device.image_update_state.version, timestamp_ms
                    )
                    image_version = str(max(int(image_version), int(device_version)))
            task.image_version = image_version

        # creates a database entry, then submits to executor
        task_db = crud.task.create(
            db_session,
            submitted_time=datetime.now(timezone.utc),
            state="pending",
            task_type=task.type,
            user_session_id=user_session_id,
            task_submission_data=task.model_dump(mode="json"),
            parent_task_id=(
                task.parent_task_id if hasattr(task, "parent_task_id") else None
            ),
        )
        if task.type == "deploy_device_task":
            if task.device.target_uses_image_updates:
                if not crud.deployment_info.reserve_image_update(
                    db_session,
                    task.device.deployment_info_id,
                    task_db.id,
                    (
                        task.device.identifier
                        if task.device.source_identifier is not None
                        else None
                    ),
                ):
                    raise RuntimeError("Failed to reserve device for image deployment")
            elif task.device.source_identifier is not None:
                crud.deployment_info.update(
                    db_session,
                    task.device.deployment_info_id,
                    pending_config_id=task.device.identifier,
                )

        subtasks: list[db_models.Task] = []

        if task.type == "deploy_devices_task":
            children_uids = []
            for device in task.devices:
                access_client_token = get_or_create_access_client_token(
                    db_session,
                    deployment_info_id=device.deployment_info_id,
                )
                submission_data = DeployDeviceTaskSubmission(
                    device=device,
                    project_path=task.project_path,
                    known_hosts_path=task.known_hosts_path,
                    ssh_key_path=task.ssh_key_path,
                    controller_access_client_endpoint=self.access_client_endpoint,
                    controller_ssh_pubkey=task.controller_ssh_pubkey,
                    parent_task_id=task_db.id,
                    access_client_token=access_client_token.token,
                    config_commit=task.config_commit,
                    image_version=task.image_version,
                )
                subtask = crud.task.create(
                    db_session,
                    submitted_time=datetime.now(timezone.utc),
                    state="pending",
                    task_type="deploy_device_task",
                    user_session_id=user_session_id,
                    task_submission_data=submission_data.model_dump(mode="json"),
                    parent_task_id=task_db.id,
                )
                access_client_token.deploy_device_task_id = subtask.id
                db_session.add(access_client_token)
                db_session.commit()
                if device.target_uses_image_updates and not (
                    crud.deployment_info.reserve_image_update(
                        db_session, device.deployment_info_id, subtask.id
                    )
                ):
                    raise RuntimeError("Failed to reserve device for image deployment")
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
        self.submit(task_data, task.user_session_id, db_session)

    if "RUNNING_IN_PLAYWRIGHT" in os.environ:

        def delete_all_tasks(self, db_session: Session):
            task_ids = []
            for task in crud.task.get_all_tasks(db_session):
                # save their ids
                task_ids.append(task.id)
            # while there are still alive tasks, spam cancel them
            while crud.task.get_all_alive_tasks(db_session):
                for task_id in task_ids:
                    self.executor.cancel_task(task_id)
                time.sleep(0.1)
            crud.task.delete_all_tasks(db_session)
