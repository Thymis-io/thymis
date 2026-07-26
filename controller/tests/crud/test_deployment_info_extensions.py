import uuid

from thymis_controller import db_models
from thymis_controller.crud import deployment_info as crud


def _make_di(db_session):
    di = db_models.DeploymentInfo(
        ssh_public_key=f"ssh-ed25519 AAAA{uuid.uuid4().hex}",
        deployed_config_id="cfg",
    )
    db_session.add(di)
    db_session.commit()
    db_session.refresh(di)
    return di


def test_update_location(db_session):
    di = _make_di(db_session)
    updated = crud.update(db_session, di.id, location="Server Room A")
    assert updated.location == "Server Room A"


def test_update_location_to_none(db_session):
    di = _make_di(db_session)
    crud.update(db_session, di.id, location="Old Location")
    updated = crud.update(db_session, di.id, location=None)
    assert updated.location is None


def test_update_stores_network_interfaces(db_session):
    di = _make_di(db_session)
    ifaces = [
        {
            "interface": "eth0",
            "ipv4_addresses": ["192.168.1.1"],
            "ipv6_addresses": [],
            "mac_address": "aa:bb:cc:dd:ee:ff",
        }
    ]
    updated = crud.update(db_session, di.id, network_interfaces=ifaces)
    assert updated.network_interfaces == ifaces


def test_update_image_state_and_clear_pending_fields(db_session):
    di = _make_di(db_session)
    task_id = uuid.uuid4()
    state = {
        "strategy": "raspberry-pi-tryboot",
        "image_id": "thymis",
        "version": "2",
        "boot_partition": 3,
        "trial": True,
    }

    updated = crud.update(
        db_session,
        di.id,
        image_update_state=state,
        pending_image_version="2",
        pending_image_task_id=task_id,
        pending_image_config_id="cfg-b",
        pending_image_config_commit="abc123",
    )
    assert updated.image_update_state == state
    assert updated.pending_image_task_id == task_id

    cleared = crud.update(
        db_session,
        di.id,
        pending_image_version=None,
        pending_image_task_id=None,
        pending_image_config_id=None,
        pending_image_config_commit=None,
    )
    assert cleared.pending_image_version is None
    assert cleared.pending_image_task_id is None
    assert cleared.pending_image_config_id is None
    assert cleared.pending_image_config_commit is None
