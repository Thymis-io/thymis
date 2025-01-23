from unittest import mock

import pytest
from sqlalchemy.orm import Session
from thymis_controller import crud, db_models, models
from thymis_controller.dependencies import get_db_session, get_project
from thymis_controller.project import Project


# monkey patch the determine_first_host_with_key
def mock_determine_first_host_with_key(hosts, public_key):
    return hosts[0]


def mock_check_device_reference(dflake_path, commit_hash: str, config_id: str):
    return True


def verify_ssh_host_key_and_creds(
    self,
    host: str,
    public_key: str,
    port: int = 22,
    username: str = "root",
    pkey=None,
):
    return True


@mock.patch(
    "thymis_controller.routers.agent.check_device_reference",
    mock_check_device_reference,
)
@mock.patch(
    "thymis_controller.routers.agent.determine_first_host_with_key",
    mock_determine_first_host_with_key,
)
@mock.patch(
    "thymis_controller.project.Project.verify_ssh_host_key_and_creds",
    verify_ssh_host_key_and_creds,
)
@mock.patch(
    "paramiko.PKey.from_path",
    lambda a: None,
)
def test_device_notify(test_client):
    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    db_session = next(db_session_func())
    crud.agent_token.create(db_session, "a", "b", "c")
    json_data = {
        "token": "c",
        "config_id": "test",
        "commit_hash": "test",
        "hardware_ids": {"pi-serial-number": "test"},
        "public_key": "test",
        "ip_addresses": ["127.0.0.1"],
    }

    assert models.DeviceNotifyRequest.model_validate(json_data) is not None
    response = test_client.post("/agent/notify", json=json_data)
    print(response.json())
    assert response.status_code == 200

    assert (
        crud.deployment_info.check_if_ssh_public_key_exists(db_session, "test") is True
    )
