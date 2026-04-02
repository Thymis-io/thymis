"""
Route-level conftest: provides a working test_client without needing
the Project fixture (which requires a real Engine, not a Session).
The new device-details endpoints don't use ProjectAD, so we can
override get_project with a simple None-returning mock.
"""
import pytest
from fastapi.testclient import TestClient
from thymis_controller.dependencies import (
    get_db_session,
    get_project,
    require_valid_user_session,
)


@pytest.fixture(scope="function")
def test_client(db_session) -> TestClient:
    """Test client that overrides DB session and stubs out auth/project."""
    from thymis_controller.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_project():
        return None

    def override_authenticate():
        return True

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_project] = override_get_project
    app.dependency_overrides[require_valid_user_session] = override_authenticate
    yield TestClient(app)
    app.dependency_overrides.clear()
