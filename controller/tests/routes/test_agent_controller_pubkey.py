import pathlib

import pytest
import requests
from thymis_agent import controller_key, enrollment, storage, systemd
from thymis_agent.constants import CONTROLLER_PUBLIC_KEY_FILENAME

PUBKEY = "ssh-ed25519 AAAAcontroller controller@thymis"
OTHER_PUBKEY = "ssh-ed25519 AAAArotated controller@thymis"


@pytest.fixture
def device(monkeypatch, tmp_path):
    data_path = tmp_path / "etc-thymis"
    data_path.mkdir()
    authorized_keys_path = str(tmp_path / "root/.ssh/authorized_keys")
    for module in (storage, controller_key):
        monkeypatch.setattr(module, "DEFAULT_DATA_PATH", data_path)
        monkeypatch.setattr(module, "AGENT_DATA_PATHS", [data_path])
    monkeypatch.setattr(
        controller_key, "ROOT_AUTHORIZED_KEYS_PATH", authorized_keys_path
    )
    return data_path


def _authorized_keys() -> str:
    path = pathlib.Path(controller_key.ROOT_AUTHORIZED_KEYS_PATH)
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
    controller_key.store_controller_public_key(PUBKEY)
    controller_key.load_controller_public_key_into_root_authorized_keys()

    assert (device / CONTROLLER_PUBLIC_KEY_FILENAME).exists()
    assert _authorized_keys().splitlines() == [PUBKEY]


def test_loading_twice_does_not_duplicate_the_key(device):
    controller_key.store_controller_public_key(PUBKEY)
    controller_key.load_controller_public_key_into_root_authorized_keys()
    controller_key.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [PUBKEY]


def test_existing_authorized_keys_are_kept(device):
    keys_path = pathlib.Path(controller_key.ROOT_AUTHORIZED_KEYS_PATH)
    keys_path.parent.mkdir(parents=True)
    keys_path.write_text("ssh-ed25519 AAAAoperator operator@laptop\n", encoding="utf-8")

    controller_key.store_controller_public_key(PUBKEY)
    controller_key.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [
        "ssh-ed25519 AAAAoperator operator@laptop",
        PUBKEY,
    ]


def test_authorized_keys_without_trailing_newline_are_not_mangled(device):
    keys_path = pathlib.Path(controller_key.ROOT_AUTHORIZED_KEYS_PATH)
    keys_path.parent.mkdir(parents=True)
    keys_path.write_text("ssh-ed25519 AAAAoperator operator@laptop", encoding="utf-8")

    controller_key.store_controller_public_key(PUBKEY)
    controller_key.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [
        "ssh-ed25519 AAAAoperator operator@laptop",
        PUBKEY,
    ]


def test_missing_key_file_leaves_authorized_keys_alone(device):
    controller_key.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys() == ""


def test_refresh_replaces_a_rotated_key(device, monkeypatch):
    controller_key.store_controller_public_key(PUBKEY)
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: FakeResponse({"controller_ssh_pubkey": OTHER_PUBKEY}),
    )

    controller_key.refresh_controller_public_key("http://controller", "thymis-token")

    stored = (device / CONTROLLER_PUBLIC_KEY_FILENAME).read_text(encoding="utf-8")
    assert stored.strip() == OTHER_PUBKEY


def test_rotation_deauthorizes_the_previous_controller_key(device, monkeypatch):
    keys_path = pathlib.Path(controller_key.ROOT_AUTHORIZED_KEYS_PATH)
    keys_path.parent.mkdir(parents=True)
    keys_path.write_text("ssh-ed25519 AAAAoperator operator@laptop\n", encoding="utf-8")
    controller_key.store_controller_public_key(PUBKEY)
    controller_key.load_controller_public_key_into_root_authorized_keys()
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: FakeResponse({"controller_ssh_pubkey": OTHER_PUBKEY}),
    )

    controller_key.refresh_controller_public_key("http://controller", "thymis-token")
    controller_key.load_controller_public_key_into_root_authorized_keys()

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

    monkeypatch.setattr(requests, "get", fake_get)

    controller_key.refresh_controller_public_key("http://controller/", "thymis-token")

    assert seen["url"] == "http://controller/agent/controller-ssh-pubkey"
    assert seen["headers"] == {"x-thymis-token": "thymis-token"}


def test_unreachable_controller_keeps_the_previous_key(device, monkeypatch):
    controller_key.store_controller_public_key(PUBKEY)

    def fake_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError("offline")

    monkeypatch.setattr(requests, "get", fake_get)

    controller_key.refresh_controller_public_key("http://controller", "thymis-token")
    controller_key.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [PUBKEY]


def test_keyless_controller_keeps_the_previous_key(device, monkeypatch):
    controller_key.store_controller_public_key(PUBKEY)
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: FakeResponse({"controller_ssh_pubkey": None}),
    )

    controller_key.refresh_controller_public_key("http://controller", "thymis-token")
    controller_key.load_controller_public_key_into_root_authorized_keys()

    assert _authorized_keys().splitlines() == [PUBKEY]


def test_enroll_returns_the_controller_pubkey(device, monkeypatch):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse(
            {"token": "thymis-" + "a" * 128, "controller_ssh_pubkey": PUBKEY}
        ),
    )

    token, controller_pubkey = enrollment.enroll(
        "http://controller", "CODE", "nonce", systemd.SystemdNotifier()
    )

    assert token == "thymis-" + "a" * 128
    assert controller_pubkey == PUBKEY


def test_enroll_against_an_old_controller_yields_no_key(device, monkeypatch):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse({"token": "thymis-" + "a" * 128}),
    )

    _, controller_pubkey = enrollment.enroll(
        "http://controller", "CODE", "nonce", systemd.SystemdNotifier()
    )

    assert controller_pubkey is None
