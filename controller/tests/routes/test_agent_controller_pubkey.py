import pathlib

import pytest
import requests
import thymis_agent.agent as agent

PUBKEY = "ssh-ed25519 AAAAcontroller controller@thymis"
OTHER_PUBKEY = "ssh-ed25519 AAAArotated controller@thymis"


@pytest.fixture
def device(monkeypatch, tmp_path):
    data_path = tmp_path / "etc-thymis"
    data_path.mkdir()
    monkeypatch.setattr(agent, "DEFAULT_DATA_PATH", data_path)
    monkeypatch.setattr(agent, "AGENT_DATA_PATHS", [data_path])
    monkeypatch.setattr(
        agent, "ROOT_AUTHORIZED_KEYS_PATH", str(tmp_path / "root/.ssh/authorized_keys")
    )
    return data_path


def _authorized_keys() -> str:
    path = pathlib.Path(agent.ROOT_AUTHORIZED_KEYS_PATH)
    return path.read_text(encoding="utf-8") if path.exists() else ""


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_stored_key_reaches_root_authorized_keys(device):
    agent.store_controller_public_key(PUBKEY)
    agent.load_controller_public_key_into_root_authorized_keys()

    assert (device / agent.CONTROLLER_PUBLIC_KEY_FILENAME).exists()
    assert _authorized_keys().splitlines() == [PUBKEY]


def test_loading_twice_does_not_duplicate_the_key(device):
    agent.store_controller_public_key(PUBKEY)
    agent.load_controller_public_key_into_root_authorized_keys()
    agent.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [PUBKEY]


def test_existing_authorized_keys_are_kept(device):
    keys_path = pathlib.Path(agent.ROOT_AUTHORIZED_KEYS_PATH)
    keys_path.parent.mkdir(parents=True)
    keys_path.write_text("ssh-ed25519 AAAAoperator operator@laptop\n", encoding="utf-8")

    agent.store_controller_public_key(PUBKEY)
    agent.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [
        "ssh-ed25519 AAAAoperator operator@laptop",
        PUBKEY,
    ]


def test_authorized_keys_without_trailing_newline_are_not_mangled(device):
    keys_path = pathlib.Path(agent.ROOT_AUTHORIZED_KEYS_PATH)
    keys_path.parent.mkdir(parents=True)
    keys_path.write_text("ssh-ed25519 AAAAoperator operator@laptop", encoding="utf-8")

    agent.store_controller_public_key(PUBKEY)
    agent.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [
        "ssh-ed25519 AAAAoperator operator@laptop",
        PUBKEY,
    ]


def test_missing_key_file_leaves_authorized_keys_alone(device):
    agent.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys() == ""


def test_refresh_replaces_a_rotated_key(device, monkeypatch):
    agent.store_controller_public_key(PUBKEY)
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: FakeResponse({"controller_ssh_pubkey": OTHER_PUBKEY}),
    )

    agent.refresh_controller_public_key("http://controller", "thymis-token")

    stored = (device / agent.CONTROLLER_PUBLIC_KEY_FILENAME).read_text(encoding="utf-8")
    assert stored.strip() == OTHER_PUBKEY


def test_rotation_deauthorizes_the_previous_controller_key(device, monkeypatch):
    keys_path = pathlib.Path(agent.ROOT_AUTHORIZED_KEYS_PATH)
    keys_path.parent.mkdir(parents=True)
    keys_path.write_text("ssh-ed25519 AAAAoperator operator@laptop\n", encoding="utf-8")
    agent.store_controller_public_key(PUBKEY)
    agent.load_controller_public_key_into_root_authorized_keys()
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: FakeResponse({"controller_ssh_pubkey": OTHER_PUBKEY}),
    )

    agent.refresh_controller_public_key("http://controller", "thymis-token")
    agent.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [
        "ssh-ed25519 AAAAoperator operator@laptop",
        OTHER_PUBKEY,
    ]


def test_refresh_sends_the_agent_token(device, monkeypatch):
    seen = {}

    def fake_get(url, headers=None, timeout=None):
        seen["url"] = url
        seen["headers"] = headers
        return FakeResponse({"controller_ssh_pubkey": PUBKEY})

    monkeypatch.setattr(agent.requests, "get", fake_get)

    agent.refresh_controller_public_key("http://controller/", "thymis-token")

    assert seen["url"] == "http://controller/agent/controller-ssh-pubkey"
    assert seen["headers"] == {"x-thymis-token": "thymis-token"}


def test_unreachable_controller_keeps_the_previous_key(device, monkeypatch):
    agent.store_controller_public_key(PUBKEY)

    def fake_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError("offline")

    monkeypatch.setattr(agent.requests, "get", fake_get)

    agent.refresh_controller_public_key("http://controller", "thymis-token")
    agent.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [PUBKEY]


def test_keyless_controller_keeps_the_previous_key(device, monkeypatch):
    agent.store_controller_public_key(PUBKEY)
    monkeypatch.setattr(
        agent.requests,
        "get",
        lambda *args, **kwargs: FakeResponse({"controller_ssh_pubkey": None}),
    )

    agent.refresh_controller_public_key("http://controller", "thymis-token")
    agent.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [PUBKEY]


def test_enroll_returns_the_controller_pubkey(device, monkeypatch):
    monkeypatch.setattr(
        agent.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(
            {"token": "thymis-" + "a" * 128, "controller_ssh_pubkey": PUBKEY}
        ),
    )

    token, controller_pubkey = agent.enroll(
        "http://controller", "CODE", "nonce", agent.SystemdNotifier()
    )

    assert token == "thymis-" + "a" * 128
    assert controller_pubkey == PUBKEY


def test_enroll_against_an_old_controller_yields_no_key(device, monkeypatch):
    monkeypatch.setattr(
        agent.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({"token": "thymis-" + "a" * 128}),
    )

    _, controller_pubkey = agent.enroll(
        "http://controller", "CODE", "nonce", agent.SystemdNotifier()
    )

    assert controller_pubkey is None
