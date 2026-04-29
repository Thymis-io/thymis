import uuid
from datetime import datetime, timezone
from multiprocessing import Pipe

from thymis_controller import crud, db_models, models
from thymis_controller.models import task as task_models
from thymis_controller.task.executor import TaskWorkerPoolManager


class FakeController:
    pass


def _make_switch_task(db_session, deployment_info_id):
    task_data = models.DeployDeviceTaskSubmission(
        device=models.DeployDeviceInformation(
            identifier="config-b",
            source_identifier="config-a",
            deployment_info_id=deployment_info_id,
            deployment_public_key="key-a",
            secrets=[],
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
        start_time=datetime.now(timezone.utc),
        state="running",
        task_type=task_data.type,
        user_session_id=uuid.uuid4(),
        task_submission_data=task_data.model_dump(mode="json"),
    )
    db_session.add(task)
    db_session.commit()
    return task


def test_failed_switch_task_clears_pending_config_id(db_session):
    deployment_info = crud.deployment_info.create(
        db_session,
        ssh_public_key="key-a",
        deployed_config_id="config-a",
    )
    crud.deployment_info.update(
        db_session,
        deployment_info.id,
        pending_config_id="config-b",
    )
    task = _make_switch_task(db_session, deployment_info.id)

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
    assert updated.deployed_config_id == "config-a"
    assert failed_task.state == "failed"
    assert "Agent failed to switch" in failed_task.exception
