from unittest import mock

from sqlalchemy.orm import Session
from thymis_controller import crud, db_models, models
from thymis_controller.dependencies import get_db_session


# monkey patch the determine_first_host_with_key
def mock_determine_first_host_with_key(hosts, public_key):
    return hosts[0]


def test_register_device(test_client):
    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    db_session = next(db_session_func())

    image = crud.image.create(
        db_session=db_session,
        build_hash="test_hash",
        identifier="test_identifier",
        commit_hash="test_commit_hash",
        device_state={},
    )

    register_request = {
        "public_key": "test_public_key",
        "build_hash": "test_hash",
        "ip_addresses": [],
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
    assert hostkey.build_hash == "test_hash"


def test_heartbeat(test_client):
    heartbeat_request = {
        "public_key": "public_key",
        "ip_addresses": ["127.0.0.1"],
    }

    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    db_session = next(db_session_func())

    crud.hostkey.create(
        db_session=db_session,
        identifier="test_identifier",
        build_hash="test_hash",
        public_key=heartbeat_request["public_key"],
        device_host="127.0.0.1",
    )

    assert models.DeviceHeartbeatRequest.model_validate(heartbeat_request) is not None

    with mock.patch(
        "thymis_controller.routers.agent.determine_first_host_with_key",
        mock_determine_first_host_with_key,
    ):
        response = test_client.post("/agent/heartbeat", json=heartbeat_request)
    assert response.status_code == 200
