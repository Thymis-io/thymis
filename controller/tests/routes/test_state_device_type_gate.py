"""API tests for protecting deployed connected devices from device-type changes."""

import subprocess
import tempfile
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
    require_valid_user_session,
)
from thymis_controller.models.state import Config, State
from thymis_controller.notifications import NotificationManager
from thymis_controller.project import Project


class FakeNetworkRelay:
    """Minimal stub for connected-device lookups."""

    def __init__(self):
        self.public_key_to_connection_id: dict[str, str] = {}


def _make_config(identifier, device_type="generic-x86_64"):
    return Config(
        displayName=identifier.replace("-", " ").title(),
        identifier=identifier,
        modules=[
            {
                "type": "thymis_controller.modules.thymis.ThymisDevice",
                "settings": {"device_type": device_type},
            }
        ],
        tags=[],
    )


def _write_state(project, configs):
    project.repo.pause_file_watcher()
    state = State(configs=configs)
    project.write_state(state)
    project.repo.add(".")
    project.repo.commit("test: set state")
    project.repo.resume_file_watcher()
    return state


@pytest.fixture()
def state_gate_client(monkeypatch):
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
    monkeypatch.setattr(global_settings, "PROJECT_PATH", project_path)
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
    project = Project(project_path, NotificationManager(), engine)
    fake_network_relay = FakeNetworkRelay()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    def override_get_project():
        return project

    def override_get_network_relay():
        return fake_network_relay

    def override_authenticate():
        return True

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_project] = override_get_project
    app.dependency_overrides[get_network_relay] = override_get_network_relay
    app.dependency_overrides[require_valid_user_session] = override_authenticate

    client = TestClient(app, raise_server_exceptions=False)
    client._project = project
    client._testing_session = TestingSession
    client._fake_network_relay = fake_network_relay
    try:
        yield client
    finally:
        for key in [
            get_db_session,
            get_project,
            get_network_relay,
            require_valid_user_session,
        ]:
            app.dependency_overrides.pop(key, None)
        tmpdir.cleanup()


def _create_deployment_info(client, config_id, ssh_public_key="ssh-key-1"):
    with client._testing_session() as session:
        deployment_info = crud.deployment_info.create(
            session,
            ssh_public_key=ssh_public_key,
            deployed_config_id=config_id,
            reachable_deployed_host="10.0.0.1",
        )
        return deployment_info.id


class TestStateDeviceTypeGate:
    def test_changing_device_type_for_connected_config_returns_400(
        self, state_gate_client
    ):
        client = state_gate_client
        _write_state(client._project, [_make_config("config-a")])
        dep_id = _create_deployment_info(client, "config-a")
        client._fake_network_relay.public_key_to_connection_id["ssh-key-1"] = "conn-1"

        new_state = State(
            configs=[_make_config("config-a", device_type="raspberry-pi-4")]
        )
        resp = client.patch("/api/state", json=new_state.model_dump(mode="json"))

        assert resp.status_code == 400
        assert "Cannot change device type" in resp.json()["detail"]

        persisted = client.get("/api/state")
        assert persisted.status_code == 200
        assert (
            persisted.json()["configs"][0]["modules"][0]["settings"]["device_type"]
            == "generic-x86_64"
        )

        with client._testing_session() as session:
            deployment_info = crud.deployment_info.get_by_id(session, dep_id)
            assert deployment_info.deployed_config_id == "config-a"

    def test_changing_device_type_for_disconnected_config_is_allowed(
        self, state_gate_client
    ):
        client = state_gate_client
        _write_state(client._project, [_make_config("config-a")])
        _create_deployment_info(client, "config-a")

        new_state = State(
            configs=[_make_config("config-a", device_type="raspberry-pi-4")]
        )
        resp = client.patch("/api/state", json=new_state.model_dump(mode="json"))

        assert resp.status_code == 200, resp.text
        assert (
            resp.json()["configs"][0]["modules"][0]["settings"]["device_type"]
            == "raspberry-pi-4"
        )
