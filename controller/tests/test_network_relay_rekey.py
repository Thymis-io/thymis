"""The controller may only ask Thymis-built (image-baked token) devices to rotate
their SSH host keys. External devices keep their keys: they belong to the owner."""

import asyncio
import json
import types

import http_network_relay.network_relay as nr
import pytest
import thymis_controller.network_relay as network_relay
from thymis_agent import messages
from thymis_controller import crud, db_models
from thymis_controller.network_relay import NetworkRelay
from thymis_controller.notifications import NotificationManager

PUBLIC_KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILeEK565Rafc3wkNOTG3yfgB5V8zm3mTeUHoJ0cMFoMq"
)
OLD_HARDWARE = {"pi-serial-number": "10000000aaaaaaaa"}
NEW_HARDWARE = {"pi-serial-number": "10000000bbbbbbbb"}


class FakeWebSocket:
    def __init__(self):
        self.client = types.SimpleNamespace(host="192.0.2.1")
        self.sent = []

    async def send_text(self, text):
        self.sent.append(json.loads(text)["inner"]["kind"])

    async def close(self):
        pass


def _managed_token(db_session) -> str:
    token = f"thymis-{'a' * 128}"
    crud.agent_token.create(db_session, "commit", "config", token)
    return token


def _external_token(db_session) -> str:
    pairing_code = crud.pairing_code.create(db_session)
    token = f"thymis-{'b' * 128}"
    db_session.add(db_models.AgentToken(token=token, pairing_code_id=pairing_code.id))
    db_session.commit()
    return token


@pytest.fixture
def relay(db_session, monkeypatch):
    relay = NetworkRelay(db_session.bind, NotificationManager())
    relay.task_controller = types.SimpleNamespace(
        project=types.SimpleNamespace(
            read_state=lambda: types.SimpleNamespace(configs=[], tags=[])
        )
    )

    async def create_connection(*args, **kwargs):
        return None

    monkeypatch.setattr(relay, "create_connection", create_connection)
    monkeypatch.setattr(network_relay.paramiko.PKey, "from_path", lambda path: None)
    # the device answers SSH with the host key it presented
    monkeypatch.setattr(
        network_relay,
        "verify_alive_with_ssh_host_key_and_connection_perms",
        lambda *args, **kwargs: True,
    )
    return relay


def _start_message(token: str, hardware_ids: dict):
    return messages.EdgeAgentToRelayStartMessage(
        token=token, hardware_ids=hardware_ids, public_key=PUBLIC_KEY
    )


def _clone_while_original_is_live(relay, token: str):
    original = FakeWebSocket()
    relay.public_key_to_connection_id[PUBLIC_KEY] = "original"
    relay.registered_agent_connections["original"] = original
    clone = FakeWebSocket()
    connection_id = asyncio.run(
        relay.get_agent_msg_loop_permission_and_create_connection_id(
            _start_message(token, NEW_HARDWARE), clone
        )
    )
    return connection_id, original


def test_live_duplicate_of_managed_device_is_told_to_rekey(db_session, relay):
    connection_id, original = _clone_while_original_is_live(
        relay, _managed_token(db_session)
    )

    assert connection_id is None
    assert original.sent == ["update_public_key"]


def test_live_duplicate_of_external_device_is_refused_without_rekey(db_session, relay):
    connection_id, original = _clone_while_original_is_live(
        relay, _external_token(db_session)
    )

    assert connection_id is None
    assert original.sent == []
    assert relay.public_key_to_connection_id[PUBLIC_KEY] == "original"


def _connect_on_new_hardware(db_session, relay, monkeypatch, token: str):
    deployment_info = crud.deployment_info.create(db_session, PUBLIC_KEY)
    crud.hardware_device.create(db_session, OLD_HARDWARE, deployment_info.id)
    websocket = FakeWebSocket()

    async def accept_and_register(self, edge_agent_connection):
        connection_id = (
            await self.get_agent_msg_loop_permission_and_create_connection_id(
                _start_message(token, NEW_HARDWARE), edge_agent_connection
            )
        )
        self.registered_agent_connections[connection_id] = edge_agent_connection
        return None, connection_id

    monkeypatch.setattr(
        nr.NetworkRelay,
        "accept_ws_and_start_msg_loop_for_edge_agents",
        accept_and_register,
    )
    result = asyncio.run(relay.accept_ws_and_start_msg_loop_for_edge_agents(websocket))
    if result is not None:
        result[0].close()
    return deployment_info, websocket


def test_managed_device_on_new_hardware_is_told_to_rekey(
    db_session, relay, monkeypatch
):
    deployment_info, websocket = _connect_on_new_hardware(
        db_session, relay, monkeypatch, _managed_token(db_session)
    )

    assert websocket.sent == ["update_public_key"]
    assert (
        crud.hardware_device.find_overlapping_hardware_ids(db_session, NEW_HARDWARE)
        == []
    )


def test_external_device_on_new_hardware_keeps_its_key_and_moves(
    db_session, relay, monkeypatch
):
    deployment_info, websocket = _connect_on_new_hardware(
        db_session, relay, monkeypatch, _external_token(db_session)
    )

    assert "update_public_key" not in websocket.sent
    assert websocket.sent[-1] == "successfully_ssh_connected"
    (new_device,) = crud.hardware_device.find_overlapping_hardware_ids(
        db_session, NEW_HARDWARE
    )
    (old_device,) = crud.hardware_device.find_overlapping_hardware_ids(
        db_session, OLD_HARDWARE
    )
    assert new_device.deployment_info_id == deployment_info.id
    assert old_device.deployment_info_id is None
    assert len(crud.deployment_info.get_by_ssh_public_key(db_session, PUBLIC_KEY)) == 1
