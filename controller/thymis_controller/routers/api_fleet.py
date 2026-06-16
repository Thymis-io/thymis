from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from thymis_controller import models
from thymis_controller.crud import agent_connection as crud_agent_connection
from thymis_controller.crud import device_metric as crud_device_metric
from thymis_controller.crud import fleet_alert as crud_fleet_alert
from thymis_controller.dependencies import DBSessionAD

router = APIRouter()


@router.get(
    "/fleet/metrics", response_model=list[models.FleetMetricPoint], tags=["fleet"]
)
def get_fleet_metrics(
    db_session: DBSessionAD,
    hours: int = Query(default=24, ge=1, le=2160),
    granularity: models.MetricGranularity = Query(
        default=models.MetricGranularity.one_hour
    ),
):
    now = datetime.now(timezone.utc)
    from_time = now - timedelta(hours=hours)
    return crud_device_metric.get_fleet_metrics_downsampled(
        db_session, from_time, now, granularity
    )


@router.get(
    "/fleet/connectivity",
    response_model=list[models.ConnectivityPoint],
    tags=["fleet"],
)
def get_fleet_connectivity(
    db_session: DBSessionAD,
    hours: int = Query(default=24, ge=1, le=2160),
    buckets: int = Query(default=48, ge=1, le=200),
):
    now = datetime.now(timezone.utc)
    from_time = now - timedelta(hours=hours)
    return crud_agent_connection.get_connectivity_series(
        db_session, from_time, now, buckets
    )


@router.get(
    "/fleet/device_metrics_latest",
    response_model=list[models.FleetDeviceMetric],
    tags=["fleet"],
)
def get_fleet_device_metrics_latest(db_session: DBSessionAD):
    return crud_device_metric.get_latest_per_device(db_session)


@router.get(
    "/fleet/availability", response_model=models.FleetAvailability, tags=["fleet"]
)
def get_fleet_availability(
    db_session: DBSessionAD,
    hours: int = Query(default=24, ge=1, le=2160),
    buckets: int = Query(default=48, ge=1, le=200),
):
    now = datetime.now(timezone.utc)
    from_time = now - timedelta(hours=hours)
    return crud_agent_connection.get_availability_matrix(
        db_session, from_time, now, buckets
    )


@router.get("/fleet/alerts", response_model=list[models.FleetAlert], tags=["fleet"])
def get_fleet_alerts(db_session: DBSessionAD):
    return crud_fleet_alert.get_fleet_alerts(db_session)
