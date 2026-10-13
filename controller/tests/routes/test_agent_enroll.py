import datetime
import re

import pytest
import thymis_agent.agent as agent
from sqlalchemy.exc import IntegrityError
from thymis_controller import crud, db_models
from thymis_controller.dependencies import get_db_session
from thymis_controller.network_relay import NetworkRelay
from thymis_controller.notifications import NotificationManager

TOKEN_RE = re.compile(r"thymis-[0-9a-f]{128}")
NONCE_A = "a" * 64
NONCE_B = "b" * 64


def _db_session(test_client):
    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    return next(db_session_func())


def _enroll(test_client, code: str, nonce: str = NONCE_A):
    return test_client.post("/agent/enroll", json={"code": code, "nonce": nonce})


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

    response = _enroll(test_client, pairing_code.code)
    assert response.status_code == 200
    assert TOKEN_RE.fullmatch(response.json()["token"])

    db_session.refresh(pairing_code)
    assert pairing_code.redeemed_at is not None
    assert pairing_code.revoked is False
    assert pairing_code.device_nonce == NONCE_A


def test_unredeemed_code_holds_no_credential(db_session):
    pairing_code = crud.pairing_code.create(db_session)

    assert pairing_code.successor is None
    assert db_session.query(db_models.AgentToken).count() == 0


def test_a_pairing_code_can_only_ever_own_one_token(db_session):
    pairing_code = crud.pairing_code.create(db_session)
    db_session.add(
        db_models.AgentToken(token="thymis-first", pairing_code_id=pairing_code.id)
    )
    db_session.commit()

    # Savepoint, so the expected failure does not abort the fixture's transaction.
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(
            db_models.AgentToken(token="thymis-second", pairing_code_id=pairing_code.id)
        )


def test_enroll_twice_same_nonce_is_idempotent(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    first = _enroll(test_client, pairing_code.code)
    second = _enroll(test_client, pairing_code.code)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["token"] == second.json()["token"]
    assert db_session.query(db_models.AgentToken).count() == 1


def test_second_device_cannot_enroll_with_a_claimed_code(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    first = _enroll(test_client, pairing_code.code, NONCE_A)
    second = _enroll(test_client, pairing_code.code, NONCE_B)

    assert first.status_code == 200
    assert second.status_code == 404
    db_session.refresh(pairing_code)
    assert pairing_code.device_nonce == NONCE_A
    assert db_session.query(db_models.AgentToken).count() == 1


def test_claim_survives_a_second_devices_attempt(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    won = _enroll(test_client, pairing_code.code, NONCE_A)
    _enroll(test_client, pairing_code.code, NONCE_B)
    retried = _enroll(test_client, pairing_code.code, NONCE_A)

    assert retried.status_code == 200
    assert retried.json()["token"] == won.json()["token"]


def test_nonce_is_not_constrained_to_ascii(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    claimed = _enroll(test_client, pairing_code.code, "é" * 32)
    assert claimed.status_code == 200
    assert _enroll(test_client, pairing_code.code, NONCE_B).status_code == 404


def test_enroll_without_a_nonce_is_rejected(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    assert _enroll(test_client, pairing_code.code, "").status_code == 404
    missing = test_client.post("/agent/enroll", json={"code": pairing_code.code})
    assert missing.status_code == 422

    # Rejection must leave the code claimable.
    db_session.refresh(pairing_code)
    assert pairing_code.redeemed_at is None
    assert _enroll(test_client, pairing_code.code).status_code == 200


def test_enroll_does_not_move_redeemed_at_on_repeat(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    _enroll(test_client, pairing_code.code)
    db_session.refresh(pairing_code)
    first_redeemed_at = pairing_code.redeemed_at

    _enroll(test_client, pairing_code.code)
    db_session.refresh(pairing_code)
    assert pairing_code.redeemed_at == first_redeemed_at


def test_enroll_expired_code_404(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)
    pairing_code.expires_at = datetime.datetime.now(
        datetime.timezone.utc
    ) - datetime.timedelta(seconds=1)
    db_session.commit()

    response = _enroll(test_client, pairing_code.code)
    assert response.status_code == 404


def test_enroll_revoked_code_404(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)
    code = pairing_code.code
    assert crud.pairing_code.revoke(db_session, code) is True

    response = _enroll(test_client, code)
    assert response.status_code == 404


def test_revoking_a_redeemed_code_also_kills_its_token(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)
    token = _enroll(test_client, pairing_code.code).json()["token"]

    assert crud.pairing_code.revoke(db_session, pairing_code.code) is True

    assert crud.agent_token.check_token_validity(db_session, token) is False


def test_revoking_an_unredeemed_code_blocks_enrollment(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    assert crud.pairing_code.revoke(db_session, pairing_code.code) is True

    assert _enroll(test_client, pairing_code.code).status_code == 404
    assert db_session.query(db_models.AgentToken).count() == 0


def test_enroll_real_agent_token_404(test_client):
    db_session = _db_session(test_client)
    real_token = f"thymis-{'a' * 128}"
    crud.agent_token.create(db_session, None, None, real_token)

    response = _enroll(test_client, real_token)
    assert response.status_code == 404


def test_enroll_unknown_code_404(test_client):
    response = _enroll(test_client, "ZZZZ-ZZZZ-ZZZZ")
    assert response.status_code == 404


def test_relay_handshake_rejects_pairing_code(db_session):
    pairing_code = crud.pairing_code.create(db_session)
    assert _handshake(db_session, pairing_code.code) is None


def test_relay_handshake_accepts_redeemed_token(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)
    token = _enroll(test_client, pairing_code.code).json()["token"]

    assert _handshake(db_session, token) is not None


def test_redeemed_token_outlives_its_code(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)
    token = _enroll(test_client, pairing_code.code).json()["token"]

    pairing_code.expires_at = datetime.datetime.now(
        datetime.timezone.utc
    ) - datetime.timedelta(seconds=1)
    db_session.commit()

    assert crud.agent_token.check_token_validity(db_session, token) is True
    assert _enroll(test_client, pairing_code.code).status_code == 404


def test_logs_rejects_pairing_code_accepts_redeemed_token(test_client):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    headers = {"x-thymis-ssh-pubkey": "ssh-ed25519 AAAA test"}
    rejected = test_client.post(
        "/agent/logs",
        content="[]",
        headers={**headers, "x-thymis-token": pairing_code.code},
    )
    assert rejected.status_code == 404

    token = _enroll(test_client, pairing_code.code).json()["token"]
    accepted = test_client.post(
        "/agent/logs",
        content="[]",
        headers={**headers, "x-thymis-token": token},
    )
    assert accepted.status_code == 200


@pytest.mark.parametrize("mangle", [str.lower, lambda c: c.replace("-", "")])
def test_enroll_accepts_any_normalizable_form(test_client, mangle):
    db_session = _db_session(test_client)
    pairing_code = crud.pairing_code.create(db_session)

    response = _enroll(test_client, mangle(pairing_code.code))
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

    enrolled = _enroll(test_client, "ab cde fghij")
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
