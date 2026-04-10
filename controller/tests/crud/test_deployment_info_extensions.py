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
