import datetime
import re

import pytest
import thymis_agent.agent as agent
from thymis_controller import crud, db_models
from thymis_controller.dependencies import get_db_session
from thymis_controller.network_relay import NetworkRelay
from thymis_controller.notifications import NotificationManager

TOKEN_RE = re.compile(r"thymis-[0-9a-f]{128}")


def _db_session(test_client):
    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    return next(db_session_func())


def _start_message(token: str) -> agent.EdgeAgentToRelayStartMessage:
    return agent.EdgeAgentToRelayStartMessage(
        token=token, hardware_ids={}, public_key="ssh-ed25519 AAAA test"
    )


def _handshake(db_session, token: str) -> str | None:
    import asyncio

    relay = NetworkRelay(db_session.bind, NotificationManager())
    return asyncio.run(
        relay.get_agent_msg_loop_permission_and_create_connection_id(
            _start_message(token), edge_agent_connection=None
        )
    )


def test_enroll_valid_code_returns_real_token(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)
    assert pairing_code.redeemed_at is None

    response = test_client.post("/agent/enroll", json={"code": pairing_code.code})
    assert response.status_code == 200
    assert TOKEN_RE.fullmatch(response.json()["token"])

    db_session.refresh(pairing_code)
    assert pairing_code.redeemed_at is not None
    assert pairing_code.revoked is False


def test_pairing_code_mints_its_successor_eagerly(db_session):
    pairing_code = crud.pairing_code.create(db_session)

    successor = db_session.get(db_models.AgentToken, pairing_code.successor_id)
    assert successor is not None
    assert TOKEN_RE.fullmatch(successor.token)
    # An abandoned code must not leave a permanent credential behind.
    assert successor.expires_at == pairing_code.expires_at


def test_enroll_twice_same_code_is_idempotent(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    first = test_client.post("/agent/enroll", json={"code": pairing_code.code})
    second = test_client.post("/agent/enroll", json={"code": pairing_code.code})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["token"] == second.json()["token"]
    assert db_session.query(db_models.AgentToken).count() == 1


def test_enroll_does_not_move_redeemed_at_on_repeat(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    test_client.post("/agent/enroll", json={"code": pairing_code.code})
    db_session.refresh(pairing_code)
    first_redeemed_at = pairing_code.redeemed_at

    test_client.post("/agent/enroll", json={"code": pairing_code.code})
    db_session.refresh(pairing_code)
    assert pairing_code.redeemed_at == first_redeemed_at


def test_enroll_expired_code_404(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)
    pairing_code.expires_at = datetime.datetime.now(
        datetime.timezone.utc
    ) - datetime.timedelta(seconds=1)
    db_session.commit()

    response = test_client.post("/agent/enroll", json={"code": pairing_code.code})
    assert response.status_code == 404


def test_enroll_revoked_code_404(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)
    code = pairing_code.code
    assert crud.pairing_code.revoke(db_session, code) is True

    response = test_client.post("/agent/enroll", json={"code": code})
    assert response.status_code == 404


def test_revoking_unredeemed_code_also_kills_its_token(db_session):
    pairing_code = crud.pairing_code.create(db_session)
    successor_token = pairing_code.successor.token

    crud.pairing_code.revoke(db_session, pairing_code.code)

    assert crud.agent_token.check_token_validity(db_session, successor_token) is False


def test_enroll_consumed_code_404(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)
    crud.pairing_code.consume(db_session, pairing_code.successor)

    response = test_client.post("/agent/enroll", json={"code": pairing_code.code})
    assert response.status_code == 404


def test_enroll_real_agent_token_404(test_client):
    db_session = _db_session(test_client)
    real_token = f"thymis-{'a' * 128}"
    crud.agent_token.create(db_session, None, None, real_token)

    response = test_client.post("/agent/enroll", json={"code": real_token})
    assert response.status_code == 404


def test_enroll_unknown_code_404(test_client):
    response = test_client.post("/agent/enroll", json={"code": "ZZZZ-ZZZZ-ZZZZ"})
    assert response.status_code == 404


def test_relay_handshake_rejects_pairing_code(db_session):
    pairing_code = crud.pairing_code.create(db_session)
    assert _handshake(db_session, pairing_code.code) is None


def test_relay_handshake_accepts_successor_token(db_session):
    pairing_code = crud.pairing_code.create(db_session)
    assert _handshake(db_session, pairing_code.successor.token) is not None


def test_consume_revokes_code_and_promotes_successor(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)
    successor = pairing_code.successor
    assert successor.expires_at is not None

    crud.pairing_code.consume(db_session, successor)

    db_session.refresh(pairing_code)
    assert pairing_code.revoked is True
    assert successor.expires_at is None
    assert crud.agent_token.check_token_validity(db_session, successor.token) is True

    response = test_client.post("/agent/enroll", json={"code": pairing_code.code})
    assert response.status_code == 404


def test_consume_is_idempotent_and_ignores_image_tokens(db_session):
    image_token = crud.agent_token.create(db_session, "commit", "config", "thymis-img")

    crud.pairing_code.consume(db_session, image_token)
    assert crud.agent_token.check_token_validity(db_session, "thymis-img") is True

    pairing_code = crud.pairing_code.create(db_session)
    crud.pairing_code.consume(db_session, pairing_code.successor)
    crud.pairing_code.consume(db_session, pairing_code.successor)
    assert (
        crud.agent_token.check_token_validity(db_session, pairing_code.successor.token)
        is True
    )


def test_logs_rejects_pairing_code_accepts_successor(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    headers = {"x-thymis-ssh-pubkey": "ssh-ed25519 AAAA test"}
    rejected = test_client.post(
        "/agent/logs",
        content="[]",
        headers={**headers, "x-thymis-token": pairing_code.code},
    )
    assert rejected.status_code == 404

    accepted = test_client.post(
        "/agent/logs",
        content="[]",
        headers={**headers, "x-thymis-token": pairing_code.successor.token},
    )
    assert accepted.status_code == 200


@pytest.mark.parametrize("mangle", [str.lower, lambda c: c.replace("-", "")])
def test_enroll_accepts_any_normalizable_form(test_client, mangle):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    response = test_client.post(
        "/agent/enroll", json={"code": mangle(pairing_code.code)}
    )
    assert response.status_code == 200
    assert response.json()["token"] == pairing_code.successor.token


def test_pairing_code_create_endpoint_does_not_leak_the_token(test_client):
    response = test_client.post("/api/pairing-code/create")
    assert response.status_code == 200
    body = response.json()
    assert not TOKEN_RE.fullmatch(body["code"])
    assert "successor_id" not in body
    assert "token" not in body


def test_code_is_stored_and_served_exactly_as_generated(test_client, monkeypatch):
    monkeypatch.setattr(
        crud.pairing_code, "generate_code", lambda *a, **kw: "AB-CDE-FGHIJ"
    )
    db_session = _db_session(test_client)

    body = test_client.post("/api/pairing-code/create").json()

    assert body["code"] == "AB-CDE-FGHIJ"
    row = db_session.query(db_models.PairingCode).one()
    assert row.code == "AB-CDE-FGHIJ"
    assert row.normalized_code == "ABCDEFGH1J"

    enrolled = test_client.post("/agent/enroll", json={"code": "ab cde fghij"})
    assert enrolled.status_code == 200


def test_agent_token_revoke_cannot_reach_a_pairing_code(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    response = test_client.post(
        "/api/agent-token/revoke", json={"token": pairing_code.code}
    )
    assert response.status_code == 404

    db_session.refresh(pairing_code)
    assert pairing_code.revoked is False


@pytest.mark.parametrize(
    "token,expected",
    [
        (f"thymis-{'a' * 128}", True),
        (f"thymis-{'A' * 128}", False),
        ("A1B2-C3D4-E5F6", False),
        (None, False),
        ("", False),
        (f"thymis-{'a' * 127}", False),
    ],
)
def test_is_real_agent_token(token, expected):
    assert agent.is_real_agent_token(token) is expected
