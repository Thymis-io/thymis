import uuid
from datetime import datetime, timedelta, timezone

from thymis_controller import db_models
from thymis_controller.crud import agent_connection as crud


def _make_di(db_session, name="dev"):
    di = db_models.DeploymentInfo(
        ssh_public_key=f"ssh-ed25519 AAAA{uuid.uuid4().hex}",
        deployed_config_id="test-config",
        name=name,
    )
    db_session.add(di)
    db_session.commit()
    db_session.refresh(di)
    return di


def test_availability_matrix_marks_online_buckets(db_session):
    di = _make_di(db_session, name="alpha")
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    db_session.add(
        db_models.AgentConnection(
            deployment_info_id=di.id,
            connected_at=base + timedelta(hours=1),
            disconnected_at=base + timedelta(hours=3),
        )
    )
    db_session.commit()

    result = crud.get_availability_matrix(
        db_session,
        from_datetime=base,
        to_datetime=base + timedelta(hours=4),
        buckets=4,
    )

    assert len(result.timestamps) == 5  # buckets + 1
    rows = {r.deployment_info_id: r for r in result.devices}
    assert di.id in rows
    states = rows[di.id].states
    # sample points at 0,1,2,3,4 hours: online while 1 <= t < 3
    assert states == [False, True, True, False, False]
    assert rows[di.id].name == "alpha"


def test_availability_matrix_still_online_connection(db_session):
    di = _make_di(db_session, name="beta")
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    # Open connection (disconnected_at is None) starting mid-window.
    db_session.add(
        db_models.AgentConnection(
            deployment_info_id=di.id,
            connected_at=base + timedelta(hours=2),
            disconnected_at=None,
        )
    )
    db_session.commit()

    result = crud.get_availability_matrix(
        db_session,
        from_datetime=base,
        to_datetime=base + timedelta(hours=4),
        buckets=4,
    )

    rows = {r.deployment_info_id: r for r in result.devices}
    # online from +2h onward, never disconnects
    assert rows[di.id].states == [False, False, True, True, True]


def test_availability_matrix_empty_window_has_no_devices(db_session):
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = crud.get_availability_matrix(
        db_session,
        from_datetime=base,
        to_datetime=base + timedelta(hours=4),
        buckets=4,
    )
    assert len(result.timestamps) == 5
    assert result.devices == []
