import sys
import uuid

from thymis_controller.task.worker import access_client_proxy_command


def test_access_client_proxy_command_uses_worker_python():
    deployment_info_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    command = access_client_proxy_command(
        "ws://127.0.0.1:8080/agent/relay", deployment_info_id
    )

    assert command == (
        f"{sys.executable} -m thymis_controller.access_client "
        f"ws://127.0.0.1:8080/agent/relay {deployment_info_id}"
    )
    assert not command.startswith("python -m thymis_controller.access_client")
