import pathlib
import uuid
from multiprocessing import Pipe
from unittest import mock

from thymis_controller import models
from thymis_controller.models import task as task_models
from thymis_controller.task import worker


def _make_task_submission(deployment_info_id):
    task_data = models.DeployDeviceTaskSubmission(
        device=models.DeployDeviceInformation(
            identifier="config-a",
            deployment_info_id=deployment_info_id,
            deployment_public_key="device-key",
            secrets=[],
        ),
        project_path="/project",
        ssh_key_path="/project/id_thymis",
        known_hosts_path="/tmp/known_hosts",
        controller_ssh_pubkey="controller-key",
        controller_access_client_endpoint="ws://127.0.0.1:8080/agent/relay_for_clients",
        access_client_token="token",
        config_commit="commit-a",
    )
    return task_models.TaskSubmission(id=uuid.uuid4(), data=task_data)


def _run_and_capture_known_hosts(extra_known_hosts):
    task = _make_task_submission(uuid.uuid4())
    controller_side, worker_side = Pipe()
    process_list = worker.ProcessList()

    captured = {}

    def fake_run_command(_task, _conn, _process_list, _cmd, _env, cwd, **_kwargs):
        captured["content"] = (pathlib.Path(cwd) / "known_hosts").read_text(
            encoding="utf-8"
        )
        return 1  # abort the task right after known_hosts is written

    with mock.patch.object(
        worker.global_settings, "EXTRA_KNOWN_HOSTS", extra_known_hosts
    ), mock.patch.object(worker, "run_command", fake_run_command):
        worker.deploy_device_task(task, worker_side, process_list)

    worker_side.close()
    controller_side.close()
    return captured["content"]


def test_deploy_device_task_includes_device_known_hosts():
    content = _run_and_capture_known_hosts([])
    lines = content.splitlines()
    assert "127.0.0.1 device-key" in lines
    assert "localhost device-key" in lines
    assert len(lines) == 2


def test_deploy_device_task_appends_extra_known_hosts_from_global_settings():
    content = _run_and_capture_known_hosts(
        ["builder.example.com ssh-ed25519 AAAABuilderKey"]
    )
    lines = content.splitlines()
    assert "127.0.0.1 device-key" in lines
    assert "localhost device-key" in lines
    assert "builder.example.com ssh-ed25519 AAAABuilderKey" in lines
    assert len(lines) == 3
