import tempfile
from unittest import mock

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker
from thymis_controller import crud, db_models, models
from thymis_controller.dependencies import get_db_session, get_project
from thymis_controller.models.state import Device

# Create an in-memory SQLite database for testing
SQLITE_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLITE_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db_session():
    """Create a new database session with a rollback at the end of the test."""
    from thymis_controller import db_models
    from thymis_controller.database.base import Base

    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    Base.metadata.create_all(bind=engine)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="module")
def project(db_session):
    from thymis_controller.project import Project

    # create temp folder
    tmpdir = tempfile.TemporaryDirectory(delete=False)
    yield Project(tmpdir.name, db_session)
    tmpdir.cleanup()


@pytest.fixture(scope="module")
def test_client(db_session, project) -> TestClient:
    """Create a test client that uses the override_get_db fixture to return a session."""
    from thymis_controller.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    def override_get_project():
        return project

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_project] = override_get_project
    return TestClient(app)


# mock an entry in the image table
@pytest.fixture(scope="module")
def mock_image_entry(db_session):
    image = crud.image.create(
        db_session,
        build_hash="test_hash",
        identifier="test-device",
        device_state={},
        commit_hash="test_commit",
    )
    db_session.add(image)
    db_session.commit()
    return {"build_hash": "test_hash", "identifier": "test-device"}


@pytest.fixture(scope="module")
def mock_hostkey_entry(db_session):
    hostkey = crud.hostkey.create(
        db_session,
        identifier="test-device-gdfgh3j9df",
        build_hash="test_hash",
        public_key="test_public",
        device_host="test_host",
    )
    db_session.add(hostkey)
    db_session.commit()
    return {
        "build_hash": "test_hash",
        "identifier": "test-device",
        "public_key": "test_public",
    }


@pytest.fixture(scope="module")
def mock_device_in_state(db_session, mock_image_entry, project):
    state = project.read_state()
    state.devices.append(
        Device(
            identifier=mock_image_entry["identifier"],
            displayName="test-device",
            tags=[],
            modules=[],
        )
    )


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
