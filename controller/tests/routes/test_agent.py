from unittest import mock

from sqlalchemy.orm import Session
from thymis_controller import crud, db_models, models
from thymis_controller.dependencies import get_db_session, get_project
from thymis_controller.project import Project


# monkey patch the determine_first_host_with_key
def mock_determine_first_host_with_key(hosts, public_key):
    return hosts[0]


def test_register_device(test_client):
    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    db_session = next(db_session_func())

    crud.image.create(
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
    assert models.RegisterDeviceRequest.model_validate(register_request) is not None
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


def test_register_clone_device(test_client, project):
    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    db_session = next(db_session_func())

    state_device = models.Device(
        identifier="test_identifier",
        displayName="test_display_name",
        modules=[],
        tags=[],
    )

    image = {
        "build_hash": "test_hash",
        "identifier": state_device.identifier,
        "commit_hash": "test_commit_hash",
        "device_state": state_device.model_dump(),
    }

    crud.image.create(db_session=db_session, **image)

    first_device = {
        "build_hash": "test_hash",
        "public_key": "test_public_key",
        "identifier": state_device.identifier,
        "device_host": "127.0.0.1",
    }

    crud.hostkey.create(db_session=db_session, **first_device, project=project)

    second_device = {
        "build_hash": "test_hash",
        "public_key": "test_public_keyClone",
        "ip_addresses": ["127.0.0.1"],
    }

    register_request = second_device
    assert models.RegisterDeviceRequest.model_validate(register_request) is not None

    with mock.patch(
        "thymis_controller.routers.agent.determine_first_host_with_key",
        mock_determine_first_host_with_key,
    ):
        response = test_client.post("/agent/register", json=register_request)
        assert response.status_code == 200

    prior_hostkey = (
        db_session.query(db_models.HostKey)
        .where(
            db_models.HostKey.build_hash == "test_hash",
            db_models.HostKey.public_key == first_device["public_key"],
        )
        .first()
    )

    assert prior_hostkey is not None
    assert prior_hostkey.build_hash == image["build_hash"]

    own_hostkey = (
        db_session.query(db_models.HostKey)
        .where(
            db_models.HostKey.build_hash == "test_hash",
            db_models.HostKey.public_key == register_request["public_key"],
        )
        .first()
    )
    assert own_hostkey is not None
    assert own_hostkey.build_hash == image["build_hash"]
    assert own_hostkey.identifier == f"{prior_hostkey.identifier}-1"


def test_register_replace_device(test_client):
    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    db_session = next(db_session_func())
    project: Project = test_client.app.dependency_overrides.get(get_project)()

    state_device = models.Device(
        identifier="test_identifier",
        displayName="test_display_name",
        modules=[],
        tags=[],
    )

    first_image = {
        "build_hash": "test_hash",
        "identifier": "test_identifier",
        "commit_hash": "test_commit_hash",
        "device_state": state_device.model_dump(),
    }

    second_image = {
        "build_hash": "test_hash_new",
        "identifier": "test_identifier",
        "commit_hash": "test_commit_hash",
        "device_state": models.Device(
            identifier="test_identifier",
            displayName="test_display_name",
            modules=[],
            tags=[],
        ).model_dump(),
    }

    crud.image.create(db_session=db_session, **first_image)
    crud.image.create(db_session=db_session, **second_image)

    first_device = {
        "build_hash": "test_hash",
        "public_key": "test_public_key",
        "identifier": first_image["identifier"],
        "device_host": "127.0.0.1",
    }

    state = project.read_state()
    state.devices.append(state_device)
    project.write_state_and_reload(state)

    crud.hostkey.create(db_session=db_session, **first_device, project=project)

    second_device = {
        "build_hash": second_image["build_hash"],
        "public_key": "public_key2",
        "ip_addresses": ["127.0.0.1"],
    }

    register_request = second_device
    assert models.RegisterDeviceRequest.model_validate(register_request) is not None

    with mock.patch(
        "thymis_controller.routers.agent.determine_first_host_with_key",
        mock_determine_first_host_with_key,
    ):
        response = test_client.post("/agent/register", json=register_request)
        assert response.status_code == 200

    prior_hostkey = (
        db_session.query(db_models.HostKey)
        .where(
            db_models.HostKey.build_hash == "test_hash",
            db_models.HostKey.public_key == first_device["public_key"],
        )
        .first()
    )

    assert prior_hostkey is not None
    assert prior_hostkey.build_hash == first_image["build_hash"]
    assert prior_hostkey.identifier == f"{first_image['identifier']}-old"

    own_hostkey = (
        db_session.query(db_models.HostKey)
        .where(
            db_models.HostKey.build_hash == register_request["build_hash"],
            db_models.HostKey.public_key == register_request["public_key"],
        )
        .first()
    )
    assert own_hostkey is not None
    assert own_hostkey.build_hash == second_image["build_hash"]
    assert own_hostkey.identifier == first_device["identifier"]


def test_heartbeat(test_client, project):
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
        project=project,
    )

    assert models.DeviceHeartbeatRequest.model_validate(heartbeat_request) is not None

    with mock.patch(
        "thymis_controller.routers.agent.determine_first_host_with_key",
        mock_determine_first_host_with_key,
    ):
        response = test_client.post("/agent/heartbeat", json=heartbeat_request)
    assert response.status_code == 200
