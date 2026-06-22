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


def test_availability_matrix_includes_unconnected_devices(db_session):
    """Non-connected non-archived devices should appear as offline."""
    di_connected = _make_di(db_session, name="connected")
    di_unconnected = _make_di(db_session, name="unconnected")
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    db_session.add(
        db_models.AgentConnection(
            deployment_info_id=di_connected.id,
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

    rows = {r.deployment_info_id: r for r in result.devices}
    # Both devices should be present
    assert di_connected.id in rows
    assert di_unconnected.id in rows
    # Connected device: online 1h-3h
    assert rows[di_connected.id].states == [False, True, True, False, False]
    # Unconnected device: always offline
    assert rows[di_unconnected.id].states == [False, False, False, False, False]


def test_availability_matrix_excludes_archived_devices(db_session):
    """Archived devices should be excluded even if they have connections."""
    di_active = _make_di(db_session, name="active")
    di_archived = _make_di(db_session, name="archived")
    di_archived.archived = True
    db_session.commit()

    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    # Give the archived device a connection in the time window
    db_session.add(
        db_models.AgentConnection(
            deployment_info_id=di_archived.id,
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

    rows = {r.deployment_info_id: r for r in result.devices}
    # Only the active device should be present
    assert di_active.id in rows
    assert di_archived.id not in rows
    # Active device with no connections should be offline
    assert rows[di_active.id].states == [False, False, False, False, False]


def test_availability_matrix_mixed_active_archived_unconnected(db_session):
    """Test with active, archived, and unconnected devices all together."""
    di_connected = _make_di(db_session, name="connected")
    di_unconnected = _make_di(db_session, name="unconnected")
    di_archived_with_conn = _make_di(db_session, name="archived-with-conn")
    di_archived_no_conn = _make_di(db_session, name="archived-no-conn")

    di_archived_with_conn.archived = True
    di_archived_no_conn.archived = True
    db_session.commit()

    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    # Give connected device a connection
    db_session.add(
        db_models.AgentConnection(
            deployment_info_id=di_connected.id,
            connected_at=base + timedelta(hours=1),
            disconnected_at=base + timedelta(hours=2),
        )
    )
    # Give archived device a connection (should still be excluded)
    db_session.add(
        db_models.AgentConnection(
            deployment_info_id=di_archived_with_conn.id,
            connected_at=base + timedelta(hours=1),
            disconnected_at=base + timedelta(hours=2),
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
    # Only non-archived devices should be present
    assert len(rows) == 2
    assert di_connected.id in rows
    assert di_unconnected.id in rows
    # Archived devices should not appear, regardless of connection history
    assert di_archived_with_conn.id not in rows
    assert di_archived_no_conn.id not in rows
    # Check states
    assert rows[di_connected.id].states == [False, True, False, False, False]
    assert rows[di_unconnected.id].states == [False, False, False, False, False]
