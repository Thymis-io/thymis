import uuid
from datetime import datetime, timedelta, timezone

from thymis_controller import db_models
from thymis_controller.crud import device_metric as crud


def _make_deployment_info(db_session):
    di = db_models.DeploymentInfo(
        ssh_public_key=f"ssh-ed25519 AAAA{uuid.uuid4().hex}",
        deployed_config_id="test-config",
    )
    db_session.add(di)
    db_session.commit()
    db_session.refresh(di)
    return di


def test_device_metric_model_exists():
    """DeviceMetric model has expected columns."""
    metric = db_models.DeviceMetric(
        deployment_info_id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        cpu_percent=42.5,
        ram_percent=67.3,
        disk_percent=10.1,
    )
    assert metric.cpu_percent == 42.5
    assert metric.ram_percent == 67.3
    assert metric.disk_percent == 10.1


def test_create_metric(db_session):
    di = _make_deployment_info(db_session)
    now = datetime.now(timezone.utc)
    metric = crud.create_metric(db_session, di.id, 50.0, 70.0, 30.0, now)
    assert metric.id is not None
    assert metric.cpu_percent == 50.0
    assert metric.ram_percent == 70.0
    assert metric.disk_percent == 30.0


def test_get_metrics_downsampled_returns_averaged_buckets(db_session):
    di = _make_deployment_info(db_session)
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    # Two entries in same 1h bucket
    crud.create_metric(db_session, di.id, 40.0, 60.0, 20.0, base)
    crud.create_metric(
        db_session, di.id, 60.0, 80.0, 40.0, base + timedelta(minutes=30)
    )

    results = crud.get_metrics_downsampled(
        db_session,
        di.id,
        from_datetime=base - timedelta(minutes=1),
        to_datetime=base + timedelta(hours=1),
        granularity="1h",
    )
    assert len(results) == 1
    assert abs(results[0]["cpu_percent"] - 50.0) < 0.01  # average of 40 and 60


def test_get_metrics_downsampled_1min_granularity(db_session):
    di = _make_deployment_info(db_session)
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    crud.create_metric(db_session, di.id, 30.0, 50.0, 10.0, base)
    crud.create_metric(
        db_session, di.id, 50.0, 70.0, 30.0, base + timedelta(seconds=30)
    )

    results = crud.get_metrics_downsampled(
        db_session,
        di.id,
        from_datetime=base - timedelta(seconds=1),
        to_datetime=base + timedelta(minutes=1),
        granularity="1min",
    )
    assert len(results) == 1
    assert abs(results[0]["cpu_percent"] - 40.0) < 0.01  # average of 30 and 50


def test_get_metrics_downsampled_15min_granularity(db_session):
    di = _make_deployment_info(db_session)
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    # Both entries fall in the same 15-minute bucket (12:00)
    crud.create_metric(db_session, di.id, 20.0, 40.0, 10.0, base)
    crud.create_metric(db_session, di.id, 40.0, 60.0, 30.0, base + timedelta(minutes=7))

    results = crud.get_metrics_downsampled(
        db_session,
        di.id,
        from_datetime=base - timedelta(seconds=1),
        to_datetime=base + timedelta(minutes=15),
        granularity="15min",
    )
    assert len(results) == 1
    assert abs(results[0]["cpu_percent"] - 30.0) < 0.01  # average of 20 and 40


def test_delete_expired_metrics(db_session):
    di = _make_deployment_info(db_session)
    old = datetime(2025, 1, 1, tzinfo=timezone.utc)
    recent = datetime.now(timezone.utc)
    crud.create_metric(db_session, di.id, 1.0, 1.0, 1.0, old)
    crud.create_metric(db_session, di.id, 2.0, 2.0, 2.0, recent)

    cutoff = datetime(2026, 1, 1, tzinfo=timezone.utc)
    deleted = crud.delete_expired_metrics(db_session, cutoff)
    assert deleted == 1

    remaining = crud.get_metrics_downsampled(
        db_session,
        di.id,
        from_datetime=datetime(2020, 1, 1, tzinfo=timezone.utc),
        to_datetime=datetime(2030, 1, 1, tzinfo=timezone.utc),
        granularity="1h",
    )
    assert len(remaining) == 1
