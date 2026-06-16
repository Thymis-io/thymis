import uuid
from datetime import datetime, timedelta, timezone

from thymis_controller import db_models
from thymis_controller.crud import fleet_alert as crud


def _make_di(db_session, name, last_seen):
    di = db_models.DeploymentInfo(
        ssh_public_key=f"ssh-ed25519 AAAA{uuid.uuid4().hex}",
        deployed_config_id="test-config",
        name=name,
        last_seen=last_seen,
    )
    db_session.add(di)
    db_session.commit()
    db_session.refresh(di)
    return di


def test_alerts_flags_prolonged_offline(db_session):
    now = datetime.now(timezone.utc)
    di = _make_di(db_session, "stale", now - timedelta(days=3))

    alerts = crud.get_fleet_alerts(db_session)
    kinds = {(a.deployment_info_id, a.kind) for a in alerts}
    assert (di.id, "offline") in kinds


def test_alerts_flags_resource_spike(db_session):
    now = datetime.now(timezone.utc)
    di = _make_di(db_session, "hot", now)
    db_session.add(
        db_models.DeviceMetric(
            deployment_info_id=di.id,
            cpu_percent=95.0,
            ram_percent=10.0,
            disk_percent=10.0,
            timestamp=now,
        )
    )
    db_session.commit()

    alerts = crud.get_fleet_alerts(db_session)
    cpu_alerts = [
        a for a in alerts if a.deployment_info_id == di.id and a.kind == "cpu"
    ]
    assert len(cpu_alerts) == 1
    assert cpu_alerts[0].severity == "critical"


def test_alerts_flags_flapping_device(db_session):
    now = datetime.now(timezone.utc)
    di = _make_di(db_session, "flapper", now)
    # More than FLAPPING_RECONNECTS_24H connect events within the window.
    for i in range(crud.FLAPPING_RECONNECTS_24H + 1):
        db_session.add(
            db_models.AgentConnection(
                deployment_info_id=di.id,
                connected_at=now - timedelta(minutes=10 * i),
                disconnected_at=now - timedelta(minutes=10 * i - 1),
            )
        )
    db_session.commit()

    alerts = crud.get_fleet_alerts(db_session)
    flapping = [
        a for a in alerts if a.deployment_info_id == di.id and a.kind == "flapping"
    ]
    assert len(flapping) == 1
    assert flapping[0].severity == "warning"


def test_alerts_does_not_flag_healthy_device(db_session):
    now = datetime.now(timezone.utc)
    di = _make_di(db_session, "healthy", now)
    db_session.add(
        db_models.DeviceMetric(
            deployment_info_id=di.id,
            cpu_percent=12.0,
            ram_percent=30.0,
            disk_percent=40.0,
            timestamp=now,
        )
    )
    db_session.commit()

    alerts = crud.get_fleet_alerts(db_session)
    assert [a for a in alerts if a.deployment_info_id == di.id] == []
