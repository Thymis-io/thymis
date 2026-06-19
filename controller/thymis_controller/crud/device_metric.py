from datetime import datetime
from uuid import UUID

from sqlalchemy import Integer, cast, func
from sqlalchemy.orm import Session
from thymis_controller import db_models, models


def _bucket_expr(granularity: str):
    """Floor each timestamp to its bucket boundary via epoch integer division."""
    bucket_seconds = models.MetricGranularity.to_seconds(granularity)
    epoch = cast(func.strftime("%s", db_models.DeviceMetric.timestamp), Integer)
    bucket_epoch = cast(epoch / bucket_seconds, Integer) * bucket_seconds
    return func.strftime(
        "%Y-%m-%dT%H:%M:%S+00:00", func.datetime(bucket_epoch, "unixepoch")
    )


def create_metric(
    db_session: Session,
    deployment_info_id: UUID,
    cpu_percent: float,
    ram_percent: float,
    disk_percent: float,
    timestamp: datetime,
) -> db_models.DeviceMetric:
    metric = db_models.DeviceMetric(
        deployment_info_id=deployment_info_id,
        cpu_percent=cpu_percent,
        ram_percent=ram_percent,
        disk_percent=disk_percent,
        timestamp=timestamp,
    )
    db_session.add(metric)
    db_session.commit()
    db_session.refresh(metric)
    return metric


def get_metrics_downsampled(
    db_session: Session,
    deployment_info_id: UUID,
    from_datetime: datetime,
    to_datetime: datetime,
    granularity: models.MetricGranularity,
) -> list[models.DeviceMetricPoint]:
    """Return averaged metrics grouped by time bucket."""
    bucket = _bucket_expr(granularity)
    rows = (
        db_session.query(
            bucket.label("bucket"),
            func.avg(db_models.DeviceMetric.cpu_percent).label("cpu_percent"),
            func.avg(db_models.DeviceMetric.ram_percent).label("ram_percent"),
            func.avg(db_models.DeviceMetric.disk_percent).label("disk_percent"),
        )
        .filter(
            db_models.DeviceMetric.deployment_info_id == deployment_info_id,
            db_models.DeviceMetric.timestamp >= from_datetime,
            db_models.DeviceMetric.timestamp <= to_datetime,
        )
        .group_by(bucket)
        .order_by(bucket.asc())
        .all()
    )
    return [
        models.DeviceMetricPoint(
            timestamp=row.bucket,
            cpu_percent=row.cpu_percent,
            ram_percent=row.ram_percent,
            disk_percent=row.disk_percent,
        )
        for row in rows
    ]


def get_latest_per_device(
    db_session: Session,
) -> list[models.FleetDeviceMetric]:
    """Return the most recent metric for each device, with the device name."""
    latest_ts = (
        db_session.query(
            db_models.DeviceMetric.deployment_info_id.label("di_id"),
            func.max(db_models.DeviceMetric.timestamp).label("max_ts"),
        )
        .group_by(db_models.DeviceMetric.deployment_info_id)
        .subquery()
    )
    rows = (
        db_session.query(db_models.DeviceMetric, db_models.DeploymentInfo)
        .join(
            latest_ts,
            (db_models.DeviceMetric.deployment_info_id == latest_ts.c.di_id)
            & (db_models.DeviceMetric.timestamp == latest_ts.c.max_ts),
        )
        .join(
            db_models.DeploymentInfo,
            db_models.DeploymentInfo.id == db_models.DeviceMetric.deployment_info_id,
        )
        .filter(db_models.DeploymentInfo.archived.is_(False))
        .all()
    )
    return [
        models.FleetDeviceMetric(
            deployment_info_id=metric.deployment_info_id,
            name=getattr(di, "name", None),
            cpu_percent=metric.cpu_percent,
            ram_percent=metric.ram_percent,
            disk_percent=metric.disk_percent,
            timestamp=metric.timestamp,
        )
        for metric, di in rows
    ]


def delete_expired_metrics(db_session: Session, cutoff_date: datetime) -> int:
    """Delete metrics older than cutoff_date. Returns number of deleted rows."""
    deleted = (
        db_session.query(db_models.DeviceMetric)
        .filter(db_models.DeviceMetric.timestamp < cutoff_date)
        .delete()
    )
    db_session.commit()
    return deleted
