"""A finished deploy_device_task reboots its device as its reboot policy asks."""

import types
import uuid
from concurrent.futures import Future
from datetime import datetime, timezone

import pytest
from thymis_controller import crud, models
from thymis_controller.task.controller import REBOOT_COMMAND, TaskController


class Fleet:
    def __init__(self, db_session, policy):
        self.db_session = db_session
        self.relay = types.SimpleNamespace(public_key_to_connection_id={})
        self.controller = TaskController(
            "http://controller", self.relay, notification_manager=None, project=None
        )
        self.executor = self.controller.executor
        self.submitted = []
        self.executor.submit = self.submitted.append
        self.executor._db_engine = db_session.bind
        self.policy = policy

    def device(self, *, reboot_required=False, online=True):
        key = f"key-{uuid.uuid4()}"
        deployment_info = crud.deployment_info.create(
            self.db_session, ssh_public_key=key, deployed_config_id="cfg"
        )
        crud.deployment_info.update(
            self.db_session, deployment_info.id, reboot_required=reboot_required
        )
        if online:
            self.relay.public_key_to_connection_id[key] = "conn"
        return deployment_info

    def deploy(self, deployment_info):
        parent = self.controller.submit(
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
                reboot_policy=self.policy,
            ),
            uuid.uuid4(),
            self.db_session,
        )
        [device_task_id] = parent.children
        return parent.id, uuid.UUID(device_task_id)

    def worker_finished(self, task_id, state):
        """Report ``task_id`` as finished with ``state`` like its worker would."""
        task = crud.task.get_task_by_id(self.db_session, task_id)
        task.state = state
        task.end_time = datetime.now(timezone.utc)
        self.db_session.commit()
        future = Future()
        self.executor.future_to_id[future] = task_id
        self.executor.futures[task_id] = (future, None)
        self.executor.listen_threads[task_id] = types.SimpleNamespace(join=lambda: None)
        self.executor.finish_task(future)
        self.db_session.expire_all()

    def task(self, task_id):
        return crud.task.get_task_by_id(self.db_session, task_id)

    def reboots(self):
        return [
            s
            for s in self.submitted
            if s.data.type == "ssh_command_task" and s.data.command == REBOOT_COMMAND
        ]


@pytest.mark.parametrize(
    "policy, reboot_required, rebooted",
    [
        ("never", True, False),
        ("if_required", False, False),
        ("if_required", True, True),
        ("always", False, True),
    ],
)
def test_policy_decides_reboot(db_session, policy, reboot_required, rebooted):
    fleet = Fleet(db_session, policy)
    deployment_info = fleet.device(reboot_required=reboot_required)
    parent_id, device_task_id = fleet.deploy(deployment_info)

    fleet.worker_finished(device_task_id, "completed")

    device_task = fleet.task(device_task_id)
    if rebooted:
        [reboot] = fleet.reboots()
        assert reboot.data.deployment_info_id == deployment_info.id
        assert device_task.children == [str(reboot.id)]
        assert fleet.task(reboot.id).parent_task_id == device_task_id
        assert device_task.state == "running"
        assert fleet.task(parent_id).state != "completed"
    else:
        assert fleet.reboots() == []
        assert device_task.state == "completed"
        assert fleet.task(parent_id).state == "completed"


def test_deploy_finishes_after_the_reboot(db_session):
    fleet = Fleet(db_session, "always")
    parent_id, device_task_id = fleet.deploy(fleet.device())
    fleet.worker_finished(device_task_id, "completed")
    [reboot] = fleet.reboots()

    fleet.worker_finished(reboot.id, "completed")

    assert fleet.task(device_task_id).state == "completed"
    assert fleet.task(parent_id).state == "completed"
    assert len(fleet.reboots()) == 1


def test_failed_reboot_fails_the_deploy(db_session):
    fleet = Fleet(db_session, "always")
    parent_id, device_task_id = fleet.deploy(fleet.device())
    fleet.worker_finished(device_task_id, "completed")
    [reboot] = fleet.reboots()

    fleet.worker_finished(reboot.id, "failed")

    assert fleet.task(device_task_id).state == "failed"
    assert fleet.task(parent_id).state == "failed"


@pytest.mark.parametrize(
    "state, online",
    [("failed", True), ("completed", False)],
    ids=["deploy-failed", "device-offline"],
)
def test_no_reboot(db_session, state, online):
    fleet = Fleet(db_session, "always")
    parent_id, device_task_id = fleet.deploy(
        fleet.device(reboot_required=True, online=online)
    )

    fleet.worker_finished(device_task_id, state)

    assert fleet.reboots() == []
    assert fleet.task(device_task_id).state == state
    assert fleet.task(parent_id).state == state
