import pytest
from thymis_controller import db_models
from thymis_controller.crud.hardware_device import find_overlapping_hardware_ids
from thymis_controller.dependencies import get_db_session


@pytest.fixture
def next_db_session(test_client):
    db_session_func = test_client.app.dependency_overrides.get(get_db_session)
    return next(db_session_func())


def create_hardware_device(db_session, hardware_ids, ssh_public_key):
    deployment_info = db_models.DeploymentInfo(ssh_public_key=ssh_public_key)
    db_session.add(deployment_info)
    db_session.commit()

    hardware_device = db_models.HardwareDevice(
        hardware_ids=hardware_ids, deployment_info_id=deployment_info.id
    )
    db_session.add(hardware_device)
    db_session.commit()
    return hardware_device


def test_no_id_in_table(db_session):
    hardware_ids = {"pi-serial-number": "id1"}
    result = find_overlapping_hardware_ids(db_session, hardware_ids)
    assert result == []


def test_one_id_in_table(db_session):
    create_hardware_device(db_session, {"pi-serial-number": "id1"}, "test_key")

    hardware_ids = {"pi-serial-number": "id1"}
    result = find_overlapping_hardware_ids(db_session, hardware_ids)
    assert len(result) == 1
    assert result[0].hardware_ids["pi-serial-number"] == "id1"


def test_two_ids_in_table_but_different(db_session):
    create_hardware_device(db_session, {"pi-serial-number": "id1"}, "test_key1")
    create_hardware_device(db_session, {"pi-serial-number": "id2"}, "test_key2")

    hardware_ids = {"pi-serial-number": "id3"}
    result = find_overlapping_hardware_ids(db_session, hardware_ids)
    assert result == []


def test_two_ids_in_table_but_same(db_session):
    create_hardware_device(db_session, {"pi-serial-number": "id1"}, "test_key1")
    create_hardware_device(db_session, {"pi-serial-number": "id2"}, "test_key2")

    hardware_ids = {"pi-serial-number": "id1"}
    result = find_overlapping_hardware_ids(db_session, hardware_ids)
    assert len(result) == 1
    assert result[0].hardware_ids["pi-serial-number"] == "id1"


def test_hardware_id_twice_in_table(db_session):
    create_hardware_device(db_session, {"pi-serial-number": "id1"}, "test_key1")
    create_hardware_device(db_session, {"pi-serial-number": "id1"}, "test_key2")

    hardware_ids = {"pi-serial-number": "id1"}
    result = find_overlapping_hardware_ids(db_session, hardware_ids)
    assert len(result) == 2
    assert all(device.hardware_ids["pi-serial-number"] == "id1" for device in result)


def test_hardware_id_twice_in_table_but_different(db_session):
    create_hardware_device(
        db_session, {"pi-serial-number": "id8", "pi-serial-number2": "id2"}, "test_key1"
    )
    create_hardware_device(
        db_session, {"pi-serial-number": "id1", "pi-serial-number2": "id3"}, "test_key2"
    )

    hardware_ids = {"pi-serial-number": "id8", "pi-serial-number2": "id3"}
    result = find_overlapping_hardware_ids(db_session, hardware_ids)
    assert len(result) == 2
    assert any(device.hardware_ids["pi-serial-number"] == "id8" for device in result)
    assert any(device.hardware_ids["pi-serial-number2"] == "id3" for device in result)


def test_hardware_id_twice_in_table_but_different1(db_session):
    create_hardware_device(
        db_session, {"pi-serial-number": "id1", "pi-serial-number2": "id2"}, "test_key1"
    )
    create_hardware_device(
        db_session, {"pi-serial-number": "id1", "pi-serial-number2": "id3"}, "test_key2"
    )

    hardware_ids = {"pi-serial-number": "id1", "pi-serial-number2": "id3"}
    result = find_overlapping_hardware_ids(db_session, hardware_ids)
    assert len(result) == 2
    assert any(device.hardware_ids["pi-serial-number"] == "id1" for device in result)
    assert any(device.hardware_ids["pi-serial-number2"] == "id3" for device in result)
