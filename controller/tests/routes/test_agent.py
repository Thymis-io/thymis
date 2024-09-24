from unittest import mock

from sqlalchemy.orm import Session
from thymis_controller import db_models, models


# monkey patch the determine_first_host_with_key
def mock_determine_first_host_with_key(hosts, public_key):
    return hosts[0]


def test_register_device(
    test_client, mock_image_entry, db_session: Session, mock_device_in_state
):
    register_request = {
        "build_hash": mock_image_entry["build_hash"],
        "public_key": "test_public_key",
        "ip_addresses": ["192.168.1.2", "192.168.1.3"],
    }
    models.RegisterDeviceRequest.model_validate(register_request)
    with mock.patch(
        "thymis_controller.routers.agent.determine_first_host_with_key",
        mock_determine_first_host_with_key,
    ):
        response = test_client.post("/agent/register", json=register_request)
        print(response.json())
        assert response.status_code == 200

    hostkey = (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.build_hash == "test_hash")
        .first()
    )
    assert hostkey is not None
    assert hostkey.build_hash == mock_image_entry["build_hash"]


def test_heartbeat(test_client, mock_hostkey_entry):
    hearbeat_request = {
        "public_key": mock_hostkey_entry["public_key"],
        "ip_addresses": ["127.0.0.1"],
    }
    with mock.patch(
        "thymis_controller.routers.agent.determine_first_host_with_key",
        mock_determine_first_host_with_key,
    ):
        response = test_client.post("/agent/heartbeat", json=hearbeat_request)
    assert response.status_code == 200
