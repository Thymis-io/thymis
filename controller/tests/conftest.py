import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker
from thymis_controller import crud
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
