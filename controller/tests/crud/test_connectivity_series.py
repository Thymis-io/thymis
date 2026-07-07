import uuid
from datetime import datetime, timedelta, timezone

from thymis_controller import db_models
from thymis_controller.crud import agent_connection as crud


def _make_di(db_session):
    di = db_models.DeploymentInfo(
        ssh_public_key=f"ssh-ed25519 AAAA{uuid.uuid4().hex}",
        deployed_config_id="test-config",
    )
    db_session.add(di)
    db_session.commit()
    db_session.refresh(di)
    return di


def _add_conn(db_session, di_id, connected_at, disconnected_at=None):
    db_session.add(
        db_models.AgentConnection(
            deployment_info_id=di_id,
            connected_at=connected_at,
            disconnected_at=disconnected_at,
        )
    )
    db_session.commit()


def test_connectivity_series_counts_overlapping(db_session):
    di_a = _make_di(db_session)
    di_b = _make_di(db_session)
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    frm = now - timedelta(hours=2)
    # A connected the whole window; B connected only in second half.
    _add_conn(db_session, di_a.id, frm - timedelta(hours=1), None)
    _add_conn(db_session, di_b.id, now - timedelta(hours=1), None)

    series = crud.get_connectivity_series(
        db_session, from_datetime=frm, to_datetime=now, buckets=2
    )
    # buckets=2 -> 3 sample points: frm, frm+1h, now
    assert len(series) == 3
    assert series[0].connected_count == 1  # only A at start
    assert series[1].connected_count == 2  # both at midpoint
    assert series[2].connected_count == 2  # both at end


def test_no_connections(db_session):
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    frm = now - timedelta(hours=2)

    series = crud.get_connectivity_series(
        db_session, from_datetime=frm, to_datetime=now, buckets=2
    )

    assert len(series) == 3
    assert series[0].connected_count == 0
    assert series[1].connected_count == 0
    assert series[2].connected_count == 0


def test_open_connection_counts_throughout(db_session):
    di = _make_di(db_session)
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    frm = now - timedelta(hours=2)
    _add_conn(db_session, di.id, frm - timedelta(hours=1), disconnected_at=None)

    series = crud.get_connectivity_series(
        db_session, from_datetime=frm, to_datetime=now, buckets=2
    )

    assert len(series) == 3
    assert series[0].connected_count == 1
    assert series[1].connected_count == 1
    assert series[2].connected_count == 1
