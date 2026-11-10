"""POST /api/action/reboot-devices targets devices, never whole configs."""

import types
import uuid

import pytest
from thymis_controller import crud
from thymis_controller.dependencies import get_network_relay, get_task_controller
from thymis_controller.task.controller import REBOOT_COMMAND, TaskController


class RecordingExecutor:
    def __init__(self):
        self.submissions = []

    def submit(self, task_submission):
        self.submissions.append(task_submission)


@pytest.fixture()
def reboot_client(test_client, db_session):
    from thymis_controller.main import app

    relay = types.SimpleNamespace(
        public_key_to_connection_id={}, registered_agent_connections={}
    )
    task_controller = TaskController(
        "http://controller", relay, notification_manager=None, project=None
    )
    task_controller.executor = RecordingExecutor()

    app.dependency_overrides[get_network_relay] = lambda: relay
    app.dependency_overrides[get_task_controller] = lambda: task_controller
    test_client.cookies.set("session-id", str(uuid.uuid4()))
    yield test_client, relay, task_controller
    app.dependency_overrides.pop(get_network_relay, None)
    app.dependency_overrides.pop(get_task_controller, None)


def _device(db_session, relay, key, config_id="shared-config", online=True):
    deployment_info = crud.deployment_info.create(
        db_session, ssh_public_key=key, deployed_config_id=config_id
    )
    if online:
        relay.public_key_to_connection_id[key] = f"conn-{key}"
    return deployment_info


def test_reboots_only_the_requested_devices(reboot_client, db_session):
    client, relay, task_controller = reboot_client
    target = _device(db_session, relay, "key-target")
    _device(db_session, relay, "key-sibling")  # same config, must not reboot
    offline = _device(db_session, relay, "key-offline", online=False)
    missing = uuid.uuid4()

    response = client.post(
        "/api/action/reboot-devices",
        params=[
            ("deployment_info_id", str(target.id)),
            ("deployment_info_id", str(target.id)),
            ("deployment_info_id", str(offline.id)),
            ("deployment_info_id", str(missing)),
        ],
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["skipped"] == [
        {"id": str(offline.id), "reason": "offline"},
        {"id": str(missing), "reason": "not_found"},
    ]

    parent, *children = task_controller.executor.submissions
    assert str(parent.id) == body["task_id"]
    assert parent.data.type == "reboot_devices_task"
    assert [child.data.deployment_info_id for child in children] == [target.id]
    assert children[0].data.command == REBOOT_COMMAND
    assert children[0].data.target_user == "root"

    child_db = crud.task.get_task_by_id(db_session, children[0].id)
    assert child_db.parent_task_id == parent.id
    assert child_db.task_type == "ssh_command_task"


def test_no_task_when_no_device_is_online(reboot_client, db_session):
    client, relay, task_controller = reboot_client
    offline = _device(db_session, relay, "key-offline", online=False)

    response = client.post(
        "/api/action/reboot-devices", params={"deployment_info_id": str(offline.id)}
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "task_id": None,
        "skipped": [{"id": str(offline.id), "reason": "offline"}],
    }
    assert task_controller.executor.submissions == []
