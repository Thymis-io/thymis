import asyncio
import uuid
from datetime import datetime, timezone

import thymis_agent.agent as agent
import thymis_controller.crud.task as crud_task
from thymis_controller import crud, models
from thymis_controller.network_relay import NetworkRelay
from thymis_controller.notifications import NotificationManager


class FakeExecutor:
    def __init__(self):
        self.messages = []

    def send_message_to_task(self, task_id, message):
        self.messages.append((task_id, message))


class FakeTaskController:
    def __init__(self):
        self.executor = FakeExecutor()


def _create_switch_task(db_session, deployment_info_id):
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
    return crud_task.create(
        db_session,
        start_time=datetime.now(timezone.utc),
        state="running",
        task_type=task_data.type,
        user_session_id=uuid.uuid4(),
        task_submission_data=task_data.model_dump(mode="json"),
        parent_task_id=None,
    )


def test_switch_activation_promotes_deployed_config_id_from_task(db_session):
    deployment_info = crud.deployment_info.create(
        db_session,
        ssh_public_key="key-a",
        deployed_config_id="config-a",
    )
    crud.deployment_info.update(
        db_session, deployment_info.id, pending_config_id="config-b"
    )
    task = _create_switch_task(db_session, deployment_info.id)

    relay = NetworkRelay(db_session.bind, NotificationManager())
    relay.connection_id_to_public_key["conn-1"] = "key-a"
    relay.task_controller = FakeTaskController()

    asyncio.run(
        relay.handle_custom_agent_message(
            agent.AgentToRelayMessage(
                inner=agent.EtRSwitchToNewConfigResultMessage(
                    task_id=task.id,
                    switch_success=True,
                    is_activated=True,
                    config_commit="commit-b",
                    stdout="",
                    stderr="activating the configuration...",
                )
            ),
            "conn-1",
        )
    )

    updated = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    assert updated.deployed_config_id == "config-b"
    assert updated.pending_config_id is None
    assert updated.deployed_config_commit == "commit-b"
    assert relay.task_controller.executor.messages
