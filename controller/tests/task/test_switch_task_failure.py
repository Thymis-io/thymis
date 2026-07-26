import threading
import uuid
from datetime import datetime, timezone
from multiprocessing import Pipe

import pytest
from thymis_agent import agent
from thymis_controller import crud, db_models, models
from thymis_controller.models import task as task_models
from thymis_controller.task.controller import TaskController
from thymis_controller.task.executor import TaskWorkerPoolManager


class FakeController:
    pass


class RecordingExecutor:
    def __init__(self):
        self.submissions = []

    def submit(self, submission):
        self.submissions.append(submission)


def _make_switch_task(db_session, deployment_info_id, *, image_update=False):
    task_data = models.DeployDeviceTaskSubmission(
        device=models.DeployDeviceInformation(
            identifier="config-b",
            source_identifier="config-a",
            deployment_info_id=deployment_info_id,
            deployment_public_key="key-a",
            secrets=[],
            target_uses_image_updates=image_update,
        ),
        project_path="/project",
        ssh_key_path="/project/id_thymis",
        known_hosts_path="/tmp/known_hosts",
        controller_ssh_pubkey="controller-key",
        controller_access_client_endpoint="ws://127.0.0.1:8080/agent/relay_for_clients",
        access_client_token="token",
        config_commit="commit-b",
    )
    task = db_models.Task(
        id=uuid.uuid4(),
        submitted_time=datetime.now(timezone.utc),
        start_time=datetime.now(timezone.utc),
        state="running",
        task_type=task_data.type,
        user_session_id=uuid.uuid4(),
        task_submission_data=task_data.model_dump(mode="json"),
    )
    db_session.add(task)
    db_session.commit()
    return task


def test_alive_deployment_task_lookup(db_session):
    deployment_info = crud.deployment_info.create(
        db_session,
        ssh_public_key="key-a",
        deployed_config_id="config-a",
    )
    task = _make_switch_task(db_session, deployment_info.id, image_update=True)

    assert crud.task.has_alive_deployment_task(db_session, deployment_info.id)
    assert crud.task.has_alive_image_config_task(db_session, "config-b")

    task.state = "completed"
    db_session.commit()
    assert not crud.task.has_alive_deployment_task(db_session, deployment_info.id)
    assert not crud.task.has_alive_image_config_task(db_session, "config-b")


def test_deploy_batch_shares_one_monotonic_image_version(db_session):
    deployments = [
        crud.deployment_info.create(
            db_session,
            ssh_public_key=f"key-{index}",
            deployed_config_id="config-a",
        )
        for index in range(2)
    ]
    task_controller = TaskController.__new__(TaskController)
    task_controller._submission_lock = threading.Lock()
    task_controller.access_client_endpoint = "ws://controller/agent/relay_for_clients"
    task_controller.executor = RecordingExecutor()
    submission = models.DeployDevicesTaskSubmission(
        devices=[
            models.DeployDeviceInformation(
                identifier="config-a",
                deployment_info_id=deployment.id,
                deployment_public_key=deployment.ssh_public_key,
                image_update_state=agent.ImageUpdateState(
                    strategy="systemd-boot",
                    image_id="thymis",
                    version=version,
                ),
                target_uses_image_updates=True,
            )
            for deployment, version in zip(
                deployments, ["9999999999999", "41"], strict=True
            )
        ],
        project_path="/project",
        ssh_key_path="/project/id_thymis",
        known_hosts_path="/project/known_hosts",
        controller_ssh_pubkey="controller-key",
        config_commit="commit-a",
    )

    task_controller.submit(submission, uuid.uuid4(), db_session)

    child_versions = {
        item.data.image_version
        for item in task_controller.executor.submissions
        if item.data.type == "deploy_device_task"
    }
    assert len(child_versions) == 1
    assert int(child_versions.pop()) > 9_999_999_999_999
    db_session.expire_all()
    assert all(
        crud.deployment_info.get_by_id(db_session, deployment.id).pending_image_task_id
        is not None
        for deployment in deployments
    )
    with pytest.raises(ValueError, match="already publishing this configuration"):
        task_controller.submit(
            models.DeployDeviceTaskSubmission(
                device=submission.devices[0],
                project_path="/project",
                ssh_key_path="/project/id_thymis",
                known_hosts_path="/project/known_hosts",
                controller_ssh_pubkey="controller-key",
                controller_access_client_endpoint=(
                    "ws://controller/agent/relay_for_clients"
                ),
                access_client_token="token",
                config_commit="commit-a",
            ),
            uuid.uuid4(),
            db_session,
        )


def test_pending_image_update_cleanup_is_task_owned(db_session):
    deployment_info = crud.deployment_info.create(
        db_session,
        ssh_public_key="key-a",
        deployed_config_id="config-a",
    )
    owner_task_id = uuid.uuid4()
    newer_task_id = uuid.uuid4()
    assert crud.deployment_info.reserve_image_update(
        db_session, deployment_info.id, owner_task_id, "config-b"
    )
    assert crud.deployment_info.set_pending_image_update(
        db_session,
        deployment_info.id,
        owner_task_id,
        version="2",
        config_id="config-b",
        config_commit="commit-b",
    )

    assert not crud.deployment_info.clear_pending_image_update(
        db_session, deployment_info.id, newer_task_id
    )
    assert not crud.deployment_info.complete_pending_image_update(
        db_session,
        deployment_info.id,
        newer_task_id,
        deployed_config_id="config-c",
        deployed_config_commit="commit-c",
    )
    db_session.expire_all()
    unchanged = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    assert unchanged.pending_image_task_id == owner_task_id
    assert unchanged.deployed_config_id == "config-a"

    assert crud.deployment_info.complete_pending_image_update(
        db_session,
        deployment_info.id,
        owner_task_id,
        deployed_config_id="config-b",
        deployed_config_commit="commit-b",
    )
    db_session.expire_all()
    completed = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    assert completed.pending_image_task_id is None
    assert completed.pending_config_id is None
    assert completed.deployed_config_id == "config-b"


def test_failed_switch_task_clears_pending_config_id(db_session):
    deployment_info = crud.deployment_info.create(
        db_session,
        ssh_public_key="key-a",
        deployed_config_id="config-a",
    )
    task = _make_switch_task(db_session, deployment_info.id, image_update=True)
    crud.deployment_info.update(
        db_session,
        deployment_info.id,
        pending_config_id="config-b",
        pending_image_version="2",
        pending_image_task_id=task.id,
        pending_image_config_id="config-b",
        pending_image_config_commit="commit-b",
    )

    executor = TaskWorkerPoolManager(FakeController())
    executor._db_engine = db_session.bind
    controller_side, worker_side = Pipe()
    worker_side.send(
        task_models.RunnerToControllerTaskUpdate(
            id=task.id,
            update=task_models.TaskFailedUpdate(reason="Agent failed to switch"),
        )
    )
    worker_side.close()
    executor.futures[task.id] = (None, controller_side)

    executor.listen_child_messages(controller_side, task.id)
    db_session.expire_all()

    updated = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    failed_task = crud.task.get_task_by_id(db_session, task.id)
    assert updated.pending_config_id is None
    assert updated.pending_image_version is None
    assert updated.pending_image_task_id is None
    assert updated.pending_image_config_id is None
    assert updated.pending_image_config_commit is None
    assert updated.deployed_config_id == "config-a"
    assert failed_task.state == "failed"
    assert "Agent failed to switch" in failed_task.exception
