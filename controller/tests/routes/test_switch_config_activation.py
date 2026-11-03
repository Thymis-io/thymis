import asyncio
import types
import uuid
from datetime import datetime, timezone

from thymis_agent import messages
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


def _create_switch_task(db_session, deployment_info_id, reboot_policy="never"):
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
        reboot_policy=reboot_policy,
    )
    return crud.task.create(
        db_session,
        submitted_time=datetime.now(timezone.utc),
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
        db_session,
        deployment_info.id,
        pending_config_id="config-b",
        name="Test Device",
    )
    task = _create_switch_task(db_session, deployment_info.id)

    relay = NetworkRelay(db_session.bind, NotificationManager())
    relay.connection_id_to_public_key["conn-1"] = "key-a"
    relay.task_controller = FakeTaskController()

    asyncio.run(
        relay.handle_custom_agent_message(
            messages.AgentToRelayMessage(
                inner=messages.EtRSwitchToNewConfigResultMessage(
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


ACTIVATED_EXIT_4_STDERR = """
Running as unit: thymis-nixos-rebuild-switch-to-configuration.service
activating the configuration...
Failed to reload dbus-broker.service
          Finished with result: exit-code
Main processes terminated with: code=exited, status=4/NOPERMISSION
"""

ACTIVATED_EXIT_1_STDERR = """
Running as unit: thymis-nixos-rebuild-switch-to-configuration.service
activating the configuration...
reloading user units for thymiskiosk...
Error: Failed to get GID for root
          Finished with result: exit-code
Main processes terminated with: code=exited, status=1/FAILURE
"""

ROLLED_BACK_STDERR = """
activating the configuration...
          Finished with result: success
Main processes terminated with: code=exited, status=0/SUCCESS

Reloading old configuration, cannot connect using new configuration
"""

INIT_CHANGED_STDERR = """
Running as unit: thymis-nixos-rebuild-switch-to-configuration.service
Warning: the new NixOS configuration has an ‘init’ that is
incompatible with the current configuration.  The new configuration
won't take effect until you reboot the system.
          Finished with result: exit-code
Main processes terminated with: code=exited, status=100/FAILURE
"""

MISSING_EXECUTABLE_STDERR = """
Running as unit: thymis-nixos-rebuild-switch-to-configuration.service
          Finished with result: exit-code
Main processes terminated with: code=exited, status=203/EXEC
"""


def _report_switch_result(
    db_session, switch_success, is_activated, stderr, reboot_policy="never"
):
    deployment_info = crud.deployment_info.create(
        db_session,
        ssh_public_key="key-a",
        deployed_config_id="config-a",
    )
    crud.deployment_info.update(
        db_session,
        deployment_info.id,
        pending_config_id="config-b",
        name="Test Device",
    )
    task = _create_switch_task(db_session, deployment_info.id, reboot_policy)

    relay = NetworkRelay(db_session.bind, NotificationManager())
    relay.connection_id_to_public_key["conn-1"] = "key-a"
    relay.connection_id_to_start_message["conn-1"] = types.SimpleNamespace(
        boot_id="boot-1"
    )
    relay.task_controller = FakeTaskController()

    asyncio.run(
        relay.handle_custom_agent_message(
            messages.AgentToRelayMessage(
                inner=messages.EtRSwitchToNewConfigResultMessage(
                    task_id=task.id,
                    switch_success=switch_success,
                    is_activated=is_activated,
                    config_commit="commit-b",
                    stdout="",
                    stderr=stderr,
                )
            ),
            "conn-1",
        )
    )
    return deployment_info, relay


def test_old_agent_tolerated_exit_4_reports_success(db_session):
    """An agent without the switch-result fix still reports a successful deploy."""
    deployment_info, relay = _report_switch_result(
        db_session,
        switch_success=False,
        is_activated=True,
        stderr=ACTIVATED_EXIT_4_STDERR,
    )

    updated = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    assert updated.deployed_config_id == "config-b"
    assert updated.pending_config_id is None
    assert updated.deployed_config_commit == "commit-b"
    assert updated.reboot_required is True
    assert "exited 4 after activation" in updated.reboot_required_reason
    assert updated.reboot_required_boot_id == "boot-1"

    notification = relay.notification_manager.queue.get_nowait()
    assert notification.data.inner.kind == "reboot_recommended"
    assert notification.data.inner.deployment_info_id == deployment_info.id
    assert "exited 4 after activation" in notification.data.inner.reason

    [(_, message)] = relay.task_controller.executor.messages
    assert message.inner.success is True


def _notification_kinds(relay):
    queue = relay.notification_manager.queue
    kinds = []
    while not queue.empty():
        kinds.append(getattr(queue.get_nowait().data.inner, "kind", None))
    return kinds


def test_no_reboot_notification_when_the_deploy_reboots(db_session):
    # tolerated exit 4: a successful switch that still needs a reboot
    deployment_info, relay = _report_switch_result(
        db_session,
        switch_success=False,
        is_activated=True,
        stderr=ACTIVATED_EXIT_4_STDERR,
        reboot_policy="if_required",
    )

    assert crud.deployment_info.get_by_id(
        db_session, deployment_info.id
    ).reboot_required
    assert "reboot_recommended" not in _notification_kinds(relay)


def test_failed_switch_still_notifies_despite_reboot_policy(db_session):
    """Failed deploys are not rebooted automatically, so the user is told."""
    _, relay = _report_switch_result(
        db_session,
        switch_success=False,
        is_activated=False,
        stderr=INIT_CHANGED_STDERR,
        reboot_policy="always",
    )

    assert "reboot_recommended" in _notification_kinds(relay)


def test_old_agent_tolerated_exit_1_reports_success(db_session):
    """A later systemd/logind error after activation is not a failed switch."""
    deployment_info, relay = _report_switch_result(
        db_session,
        switch_success=False,
        is_activated=True,
        stderr=ACTIVATED_EXIT_1_STDERR,
    )

    updated = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    assert updated.deployed_config_id == "config-b"
    assert updated.pending_config_id is None
    assert updated.deployed_config_commit == "commit-b"
    assert updated.reboot_required is True
    assert "exited 1 after activation" in updated.reboot_required_reason

    [(_, message)] = relay.task_controller.executor.messages
    assert message.inner.success is True


def test_switch_with_incompatible_init_requires_reboot(db_session):
    """Exit 100 is a failed switch, but the new init still needs a reboot."""
    deployment_info, relay = _report_switch_result(
        db_session,
        switch_success=False,
        is_activated=False,
        stderr=INIT_CHANGED_STDERR,
    )

    updated = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    assert updated.deployed_config_id == "config-a"
    assert updated.reboot_required is True
    assert "different init" in updated.reboot_required_reason

    notification = relay.notification_manager.queue.get_nowait()
    assert notification.data.inner.deployment_info_id == deployment_info.id
    assert "different init" in notification.data.inner.reason

    [(_, message)] = relay.task_controller.executor.messages
    assert message.inner.success is False


def test_reboot_clears_the_flag(db_session):
    deployment_info, _ = _report_switch_result(
        db_session,
        switch_success=False,
        is_activated=True,
        stderr=ACTIVATED_EXIT_4_STDERR,
    )
    assert crud.deployment_info.get_by_id(
        db_session, deployment_info.id
    ).reboot_required

    # reconnecting on the same boot keeps the flag
    crud.deployment_info.create_or_update_by_public_key(
        db_session, "key-a", "config-b", boot_id="boot-1"
    )
    assert crud.deployment_info.get_by_id(
        db_session, deployment_info.id
    ).reboot_required

    # reconnecting after a reboot clears it
    crud.deployment_info.create_or_update_by_public_key(
        db_session, "key-a", "config-b", boot_id="boot-2"
    )
    updated = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    assert updated.reboot_required is False
    assert updated.reboot_required_reason is None
    assert updated.reboot_required_boot_id is None


def test_old_agent_failed_switch_stays_failed(db_session):
    deployment_info, relay = _report_switch_result(
        db_session,
        switch_success=False,
        is_activated=False,
        stderr=MISSING_EXECUTABLE_STDERR,
    )

    updated = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    assert updated.deployed_config_id == "config-a"
    assert updated.pending_config_id == "config-b"
    assert updated.reboot_required is False

    [(_, message)] = relay.task_controller.executor.messages
    assert message.inner.success is False


def test_rolled_back_switch_stays_failed(db_session):
    deployment_info, relay = _report_switch_result(
        db_session,
        switch_success=False,
        is_activated=False,
        stderr=ROLLED_BACK_STDERR,
    )

    updated = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    assert updated.deployed_config_id == "config-a"
    assert updated.pending_config_id == "config-b"
    assert updated.reboot_required is False

    [(_, message)] = relay.task_controller.executor.messages
    assert message.inner.success is False


def test_legacy_reboot_flag_without_boot_id_clears_on_next_connect(db_session):
    """A flag set before boot ids were recorded clears on the next connection."""
    deployment_info = crud.deployment_info.create(
        db_session, ssh_public_key="key-a", deployed_config_id="config-a"
    )
    crud.deployment_info.update(
        db_session,
        deployment_info.id,
        reboot_required=True,
        reboot_required_reason="kernel changed",
    )

    crud.deployment_info.create_or_update_by_public_key(
        db_session, "key-a", "config-a", boot_id="boot-1"
    )

    updated = crud.deployment_info.get_by_id(db_session, deployment_info.id)
    assert updated.reboot_required is False
    assert updated.reboot_required_reason is None
    assert updated.reboot_required_boot_id is None
