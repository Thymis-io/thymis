import uuid
from datetime import datetime, timedelta, timezone

from thymis_controller import db_models
from thymis_controller.crud import device_metric as crud
from thymis_controller.models import MetricGranularity


def _make_di(db_session):
    di = db_models.DeploymentInfo(
        ssh_public_key=f"ssh-ed25519 AAAA{uuid.uuid4().hex}",
        deployed_config_id="test-config",
    )
    db_session.add(di)
    db_session.commit()
    db_session.refresh(di)
    return di


def test_latest_per_device_returns_most_recent(db_session):
    di_a = _make_di(db_session)
    di_b = _make_di(db_session)
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    crud.create_metric(db_session, di_a.id, 10.0, 20.0, 30.0, base)
    crud.create_metric(db_session, di_a.id, 70.0, 20.0, 30.0, base + timedelta(hours=1))
    crud.create_metric(db_session, di_b.id, 55.0, 60.0, 65.0, base)

    results = crud.get_latest_per_device(db_session)
    by_id = {r.deployment_info_id: r for r in results}
    assert len(results) == 2
    assert abs(by_id[di_a.id].cpu_percent - 70.0) < 0.01  # latest, not 10.0
    assert abs(by_id[di_b.id].cpu_percent - 55.0) < 0.01


def test_metric_granularity_six_hour_and_one_day_to_seconds():
    assert MetricGranularity.to_seconds(MetricGranularity.six_hour) == 6 * 60 * 60
    assert MetricGranularity.to_seconds(MetricGranularity.one_day) == 24 * 60 * 60


def test_latest_per_device_no_metrics_returns_empty(db_session):
    _make_di(db_session)
    results = crud.get_latest_per_device(db_session)
    assert results == []
