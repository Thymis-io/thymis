"""
API-level integration tests for the switch-config endpoint.

exercise the switch-config behavior through FastAPI's TestClient instead of
calling the CRUD update path directly. Test setup seeds deployment_info rows
directly so the test does not depend on Playwright-only routes.
"""

import asyncio
import subprocess
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker
from thymis_controller import crud
from thymis_controller.config import global_settings
from thymis_controller.database.base import Base
from thymis_controller.dependencies import (
    get_db_session,
    get_network_relay,
    get_project,
    get_task_controller,
    require_valid_user_session,
)
from thymis_controller.models.state import Config, State
from thymis_controller.notifications import NotificationManager
from thymis_controller.project import Project

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_state(project, configs):
    """Write a state.json with the given configs and commit so repo stays clean."""
    project.repo.pause_file_watcher()
    state = State(configs=configs)
    project.write_state(state)
    project.repo.add(".")
    project.repo.commit("test: set state")
    project.repo.resume_file_watcher()
    return state


def _make_config(identifier, displayName=None, device_type="generic-x86_64"):
    return Config(
        displayName=displayName or identifier.replace("-", " ").title(),
        identifier=identifier,
        modules=[
            {
                "type": "thymis_controller.modules.thymis.ThymisDevice",
                "settings": {"device_type": device_type},
            }
        ],
        tags=[],
    )


def _create_deployment_info(client, config_id, ssh_public_key="ssh-ed25519 AAAA"):
    """Seed deployment_info setup data, then read it back through the API."""
    with client._testing_session() as session:
        deployment_info = crud.deployment_info.create(
            session,
            ssh_public_key=ssh_public_key,
            deployed_config_id=config_id,
            reachable_deployed_host="10.0.0.1",
        )
        client._project.update_known_hosts(session)
        dep_id = deployment_info.id
    return _get_deployment_info(client, dep_id)


def _get_deployment_info(client, dep_id):
    resp = client.get(f"/api/deployment_info/{dep_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class FakeNetworkRelay:
    """Minimal stub — lets the endpoint read public_key_to_connection_id."""

    def __init__(self):
        self.public_key_to_connection_id: dict[str, str | None] = {}


class FakeTaskController:
    """Records task submissions so tests can assert what was submitted."""

    def __init__(self):
        self.submissions: list[dict] = []
        self.access_client_endpoint = "http://localhost:8000"

    def submit(self, model, user_session_id=None, db_session=None):
        task_id = uuid.uuid4()
        self.submissions.append(
            {
                "task_id": task_id,
                "model": model,
                "user_session_id": user_session_id,
            }
        )

        class _Task:
            id = task_id

        return _Task()


@pytest.fixture()
def switch_test_client(monkeypatch):
    """TestClient wired up with stubs for network_relay and task_controller.

    Creates its own engine, project, and db_session so the Project has a real
    Engine — which is what it expects for opening its own sessions.
    """
    from thymis_controller.main import app

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    tmpdir = tempfile.TemporaryDirectory(delete=False)
    project_path = Path(tmpdir.name)
    subprocess.run(
        [
            "ssh-keygen",
            "-t",
            "ed25519",
            "-f",
            str(project_path / "id_thymis"),
            "-N",
            "",
            "-C",
            "thymis-controller-test",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    monkeypatch.setattr(global_settings, "PROJECT_PATH", project_path)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    project = Project(project_path, NotificationManager(), engine)

    fake_network_relay = FakeNetworkRelay()
    fake_task_controller = FakeTaskController()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    def override_get_project():
        return project

    def override_get_task_controller():
        return fake_task_controller

    def override_get_network_relay():
        return fake_network_relay

    def override_authenticate():
        return True

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_project] = override_get_project
    app.dependency_overrides[get_task_controller] = override_get_task_controller
    app.dependency_overrides[get_network_relay] = override_get_network_relay
    app.dependency_overrides[require_valid_user_session] = override_authenticate

    client = TestClient(
        app, cookies={"session-id": str(uuid.uuid4())}, raise_server_exceptions=False
    )
    client._fake_network_relay = fake_network_relay
    client._fake_task_controller = fake_task_controller
    client._project = project
    client._testing_session = TestingSession
    try:
        yield client
    finally:
        asyncio.set_event_loop(None)
        loop.close()

    tmpdir.cleanup()
    for key in [
        get_db_session,
        get_project,
        get_task_controller,
        get_network_relay,
        require_valid_user_session,
    ]:
        app.dependency_overrides.pop(key, None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSwitchConfigAPI:
    """Exercise POST /api/action/switch-config through the HTTP layer."""

    def test_switch_config_offline_device_does_not_set_pending(
        self, switch_test_client
    ):
        """Offline devices cannot have an in-flight switch, so pending stays clear."""
        client = switch_test_client
        project = client._project
        _write_state(project, [_make_config("config-a"), _make_config("config-b")])

        dep = _create_deployment_info(client, "config-a")
        dep_id = dep["id"]

        resp = client.post(
            "/api/action/switch-config",
            params={"deployment_info_id": dep_id, "new_config_id": "config-b"},
        )
        assert resp.status_code == 409
        assert "Device is offline" in resp.json()["detail"]

        updated = _get_deployment_info(client, dep_id)
        assert updated["pending_config_id"] is None
        assert updated["deployed_config_id"] == "config-a"
        assert len(client._fake_task_controller.submissions) == 0

    def test_switch_config_device_connected_submits_task(self, switch_test_client):
        """When the device is connected, a deploy task is submitted."""
        client = switch_test_client
        project = client._project
        _write_state(project, [_make_config("config-a"), _make_config("config-b")])

        dep = _create_deployment_info(client, "config-a", ssh_public_key="ssh-key-1")

        client._fake_network_relay.public_key_to_connection_id["ssh-key-1"] = "conn-1"

        resp = client.post(
            "/api/action/switch-config",
            params={"deployment_info_id": dep["id"], "new_config_id": "config-b"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "deploy started" in body["message"]
        assert "task_id" in body

        assert len(client._fake_task_controller.submissions) == 1
        submission = client._fake_task_controller.submissions[0]
        assert submission["model"].type == "deploy_device_task"
        assert submission["model"].parent_task_id is None
        assert submission["model"].device.identifier == "config-b"
        assert submission["model"].device.source_identifier == "config-a"
        assert submission["model"].device.deployment_info_id == uuid.UUID(dep["id"])

    def test_switch_config_different_device_type_returns_400(self, switch_test_client):
        """Switching is only valid between configs for the same device type."""
        client = switch_test_client
        _write_state(
            client._project,
            [
                _make_config("config-a", device_type="raspberry-pi-4"),
                _make_config("config-b", device_type="generic-x86_64"),
            ],
        )

        dep = _create_deployment_info(client, "config-a")

        resp = client.post(
            "/api/action/switch-config",
            params={"deployment_info_id": dep["id"], "new_config_id": "config-b"},
        )

        assert resp.status_code == 400
        assert "different device types" in resp.json()["detail"]

        updated = _get_deployment_info(client, dep["id"])
        assert updated["pending_config_id"] is None
        assert len(client._fake_task_controller.submissions) == 0

    def test_switch_config_connected_task_submission_sets_pending(
        self, switch_test_client
    ):
        client = switch_test_client
        _write_state(
            client._project, [_make_config("config-a"), _make_config("config-b")]
        )
        dep = _create_deployment_info(client, "config-a", ssh_public_key="ssh-key-1")
        client._fake_network_relay.public_key_to_connection_id["ssh-key-1"] = "conn-1"

        resp = client.post(
            "/api/action/switch-config",
            params={"deployment_info_id": dep["id"], "new_config_id": "config-b"},
        )

        assert resp.status_code == 200
        updated = _get_deployment_info(client, dep["id"])
        assert updated["pending_config_id"] == "config-b"

    def test_switch_config_missing_config_returns_404(self, switch_test_client):
        client = switch_test_client
        _write_state(client._project, [_make_config("config-a")])

        dep = _create_deployment_info(client, "config-a")

        resp = client.post(
            "/api/action/switch-config",
            params={"deployment_info_id": dep["id"], "new_config_id": "nonexistent"},
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_switch_config_missing_deployment_info_returns_404(
        self, switch_test_client
    ):
        client = switch_test_client
        _write_state(
            client._project, [_make_config("config-a"), _make_config("config-b")]
        )

        fake_id = str(uuid.uuid4())
        resp = client.post(
            "/api/action/switch-config",
            params={"deployment_info_id": fake_id, "new_config_id": "config-b"},
        )
        assert resp.status_code == 404
        assert "Deployment info not found" in resp.json()["detail"]

    def test_switch_config_dirty_repo_returns_409(self, switch_test_client):
        client = switch_test_client
        project = client._project
        _write_state(project, [_make_config("config-a"), _make_config("config-b")])

        (project.repo_dir / "dirty-file.txt").write_text("dirty")

        dep = _create_deployment_info(client, "config-a")

        resp = client.post(
            "/api/action/switch-config",
            params={"deployment_info_id": dep["id"], "new_config_id": "config-b"},
        )
        assert resp.status_code == 409
        assert "dirty" in resp.json()["detail"].lower()

    def test_get_deployment_info_shows_pending(self, switch_test_client):
        """GET /api/deployment_info/{id} reflects pending_config_id."""
        client = switch_test_client
        project = client._project
        _write_state(project, [_make_config("config-a"), _make_config("config-b")])

        dep = _create_deployment_info(client, "config-a")
        assert dep["pending_config_id"] is None

        client._fake_network_relay.public_key_to_connection_id[
            dep["ssh_public_key"]
        ] = "conn-1"
        client.post(
            "/api/action/switch-config",
            params={"deployment_info_id": dep["id"], "new_config_id": "config-b"},
        )

        updated = _get_deployment_info(client, dep["id"])
        assert updated["pending_config_id"] == "config-b"

    def test_get_all_deployment_infos_shows_pending(self, switch_test_client):
        """GET /api/all_deployment_infos reflects pending_config_id."""
        client = switch_test_client
        _write_state(
            client._project, [_make_config("config-a"), _make_config("config-b")]
        )

        dep = _create_deployment_info(client, "config-a")

        client._fake_network_relay.public_key_to_connection_id[
            dep["ssh_public_key"]
        ] = "conn-1"
        client.post(
            "/api/action/switch-config",
            params={"deployment_info_id": dep["id"], "new_config_id": "config-b"},
        )

        resp = client.get("/api/all_deployment_infos")
        assert resp.status_code == 200
        infos = resp.json()
        matching = [i for i in infos if i["id"] == dep["id"]]
        assert len(matching) == 1
        assert matching[0]["pending_config_id"] == "config-b"
