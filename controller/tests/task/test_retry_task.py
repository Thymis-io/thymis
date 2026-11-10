"""Retrying a subtask starts a new top-level task."""

import types
import uuid

from thymis_controller import crud, models
from thymis_controller.task.controller import TaskController


def test_retrying_a_subtask_starts_a_top_level_task(db_session):
    relay = types.SimpleNamespace(public_key_to_connection_id={})
    controller = TaskController(
        "http://controller", relay, notification_manager=None, project=None
    )
    controller.executor.submit = lambda submission: None
    deployment_info = crud.deployment_info.create(
        db_session, ssh_public_key="key", deployed_config_id="cfg"
    )
    parent = controller.submit(
        models.DeployDevicesTaskSubmission(
            devices=[
                models.DeployDeviceInformation(
                    identifier="cfg",
                    deployment_info_id=deployment_info.id,
                    deployment_public_key=deployment_info.ssh_public_key,
                )
            ],
            project_path="/project",
            ssh_key_path="/project/id_thymis",
            known_hosts_path="/project/known_hosts",
            controller_ssh_pubkey="controller-key",
            config_commit="commit",
        ),
        uuid.uuid4(),
        db_session,
    )
    [subtask_id] = parent.children

    controller.retry_task(uuid.UUID(subtask_id), db_session)

    retried = crud.task.get_tasks_short(db_session, limit=1)[0]
    assert retried.task_type == "deploy_device_task"
    assert retried.parent_task_id is None
    assert retried.task_submission_data.parent_task_id is None
    assert crud.task.get_task_by_id(db_session, parent.id).children == [subtask_id]
