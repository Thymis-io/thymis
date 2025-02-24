import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker
from thymis_controller import crud, db_models
from thymis_controller.dependencies import (
    get_db_session,
    get_project,
    require_valid_user_session,
)
from thymis_controller.models.state import Config
from thymis_controller.notifications import NotificationManager

# Create an in-memory SQLite database for testing
SQLITE_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLITE_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def project(db_session):
    from thymis_controller.project import Project

    # create temp folder
    tmpdir = tempfile.TemporaryDirectory(delete=False)
    yield Project(tmpdir.name, NotificationManager(), db_session)
    tmpdir.cleanup()


@pytest.fixture(scope="function")
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

    def override_authenticate():
        return True

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_project] = override_get_project
    app.dependency_overrides[require_valid_user_session] = override_authenticate
    return TestClient(app)
