from datetime import datetime
from uuid import UUID

from sqlalchemy import Integer, func, literal
from sqlalchemy.orm import Session
from thymis_controller import db_models


def _bucket_expr(granularity: str):
    """Return a SQLite strftime expression grouping timestamps into buckets."""
    ts = db_models.DeviceMetric.timestamp
    if granularity == "1min":
        return func.strftime("%Y-%m-%d %H:%M", ts)
    elif granularity == "15min":
        minute_bucket = (
            func.cast(func.strftime("%M", ts), Integer)
            .op("/")(literal(15, Integer))
            .op("*")(literal(15, Integer))
        )
        return func.strftime("%Y-%m-%d %H:", ts).op("||")(
            func.printf("%02d", minute_bucket)
        )
    elif granularity == "1h":
        return func.strftime("%Y-%m-%d %H", ts)
    else:
        raise ValueError(f"Unknown granularity: {granularity!r}")


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
    granularity: str,  # "1min" | "15min" | "1h"
) -> list[dict]:
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
        {
            "timestamp": row.bucket,
            "cpu_percent": row.cpu_percent,
            "ram_percent": row.ram_percent,
            "disk_percent": row.disk_percent,
        }
        for row in rows
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
