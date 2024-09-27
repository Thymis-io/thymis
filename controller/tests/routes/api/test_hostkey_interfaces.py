from fastapi.testclient import TestClient
from thymis_controller import crud, models
from thymis_controller.dependencies import get_db_session

PATH_PREFIX = "/api/hostkey"


def test_create_hostkey(test_client):
    hostkey = models.CreateHostkeyRequest(
        public_key="test_public_key",
        device_host="test",
    )
    response = test_client.put(f"{PATH_PREFIX}/test_id", json=hostkey.model_dump())
    assert response.status_code == 200
    assert response.json()["publicKey"] == "test_public_key"

    hostkey = models.CreateHostkeyRequest(
        public_key="test_public_key2",
        device_host="test2",
    )

    response = test_client.put(f"{PATH_PREFIX}/test_id", json=hostkey.model_dump())
    assert response.status_code == 200
    assert response.json()["publicKey"] == "test_public_key2"


def test_get_hostkey_not_found(test_client):
    response = test_client.get(f"{PATH_PREFIX}/test_id")
    assert response.status_code == 404


def test_get_hostkey(test_client):
    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    db_session = next(db_session_func())

    crud.hostkey.create(
        db_session,
        "test_id",
        None,
        "test_public_key",
        "test",
    )

    response = test_client.get(f"{PATH_PREFIX}/test_id")
    assert response.status_code == 200
    assert response.json()["publicKey"] == "test_public_key"


def test_delete_hostkey(test_client):
    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    db_session = next(db_session_func())

    crud.hostkey.create(
        db_session,
        "test_id",
        None,
        "test_public_key",
        "test",
    )

    response = test_client.delete(f"{PATH_PREFIX}/test_id")
    assert response.status_code == 200


def test_delete_hostkey_not_found(test_client):
    response = test_client.get(f"{PATH_PREFIX}/test_id")
    assert response.status_code == 404
