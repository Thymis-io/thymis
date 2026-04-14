import uuid
from datetime import datetime, timezone

from thymis_controller import db_models
from thymis_controller.crud import device_metric as crud_metric


def _make_di(db_session, location=None, network_interfaces=None):
    di = db_models.DeploymentInfo(
        ssh_public_key=f"ssh-ed25519 AAAA{uuid.uuid4().hex}",
        deployed_config_id="cfg",
        location=location,
        network_interfaces=network_interfaces,
    )
    db_session.add(di)
    db_session.commit()
    db_session.refresh(di)
    return di


def test_get_connection_history(test_client, db_session):
    di = _make_di(db_session)
    # Connection without a disconnected_at (still active)
    conn_open = db_models.AgentConnection(
        deployment_info_id=di.id,
        connected_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    # Connection with both timestamps
    conn_closed = db_models.AgentConnection(
        deployment_info_id=di.id,
        connected_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        disconnected_at=datetime(2026, 1, 2, 1, 0, 0, tzinfo=timezone.utc),
    )
    db_session.add(conn_open)
    db_session.add(conn_closed)
    db_session.commit()

    response = test_client.get(f"/api/deployment_info/{di.id}/connection_history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "connected_at" in data[0]

    # Closed connection has both timestamps
    closed_entries = [e for e in data if e.get("disconnected_at") is not None]
    assert len(closed_entries) == 1
    assert closed_entries[0]["connected_at"] is not None

    # Open connection has no disconnected_at
    open_entries = [e for e in data if e.get("disconnected_at") is None]
    assert len(open_entries) == 1
    assert open_entries[0]["disconnected_at"] is None


def test_get_metrics(test_client, db_session):
    di = _make_di(db_session)
    now = datetime.now(timezone.utc)
    crud_metric.create_metric(db_session, di.id, 50.0, 60.0, 30.0, now)

    response = test_client.get(
        f"/api/deployment_info/{di.id}/metrics?hours=1&granularity=1min"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "cpu_percent" in data[0]


def test_update_location(test_client, db_session):
    di = _make_di(db_session)
    response = test_client.patch(
        f"/api/deployment_info/{di.id}",
        json={"location": "Server Room B"},
    )
    assert response.status_code == 200
    assert response.json()["location"] == "Server Room B"


def test_update_location_to_null(test_client, db_session):
    di = _make_di(db_session, location="Old Location")
    response = test_client.patch(
        f"/api/deployment_info/{di.id}",
        json={"location": None},
    )
    assert response.status_code == 200
    assert response.json()["location"] is None


def test_get_error_logs(test_client, db_session):
    di = _make_di(db_session)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    # severity=3 (Error) — should be returned by the max_severity=3 filter
    error_entry = db_models.LogEntry(
        id=uuid.uuid4(),
        timestamp=now,
        message="An error occurred",
        hostname="testhost",
        facility=3,
        severity=3,
        programname="testprog",
        syslogtag="testprog[123]:",
        deployment_info_id=di.id,
        ssh_public_key=di.ssh_public_key,
    )
    # severity=4 (Warning) — must be excluded because 4 > max_severity=3
    warning_entry = db_models.LogEntry(
        id=uuid.uuid4(),
        timestamp=now,
        message="A warning occurred",
        hostname="testhost",
        facility=3,
        severity=4,
        programname="testprog",
        syslogtag="testprog[123]:",
        deployment_info_id=di.id,
        ssh_public_key=di.ssh_public_key,
    )
    db_session.add(error_entry)
    db_session.add(warning_entry)
    db_session.commit()

    response = test_client.get(f"/api/deployment_info/{di.id}/error_logs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Only the Error entry (severity=3) should be returned; Warning (severity=4) excluded
    assert len(data) == 1
    assert data[0]["message"] == "An error occurred"
    assert data[0]["severity"] == 3
