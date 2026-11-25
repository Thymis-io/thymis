import uuid

from thymis_controller import crud, db_models

PUBKEY = "ssh-ed25519 AAAAtest homepi4"
TOKEN = "test-agent-token"


def _entry(message: str = "hello") -> dict:
    return {
        "uuid": str(uuid.uuid4()),
        "timestamp": "2026-11-25T04:31:56.833314Z",
        "message": message,
        "host": "homepi4",
        "facility": 3,
        "severity": 6,
        "programname": "test",
        "syslogtag": "test[1]:",
    }


def _post(test_client, entries, token=TOKEN):
    return test_client.post(
        "/agent/logs",
        json=entries,
        headers={
            "X-Thymis-Ssh-Pubkey": PUBKEY,
            "X-Thymis-Token": token,
            "X-Thymis-Hostname": "homepi4",
        },
    )


def test_log_batch_is_stored_and_linked_to_deployment(test_client, db_session):
    deployment = crud.deployment_info.create(db_session, PUBKEY)
    crud.agent_token.create(db_session, "commit", "config", TOKEN)

    response = _post(test_client, [_entry()])

    assert response.status_code == 200
    stored = db_session.query(db_models.LogEntry).all()
    assert len(stored) == 1
    assert stored[0].deployment_info_id == deployment.id


def test_log_batch_larger_than_chunk_size_is_stored(test_client, db_session):
    crud.agent_token.create(db_session, "commit", "config", TOKEN)

    response = _post(test_client, [_entry(f"line {i}") for i in range(501)])

    assert response.status_code == 200
    assert db_session.query(db_models.LogEntry).count() == 501


def test_log_batch_rejects_invalid_token(test_client, db_session):
    response = _post(test_client, [_entry()], token="wrong")

    assert response.status_code == 404
    assert db_session.query(db_models.LogEntry).count() == 0
