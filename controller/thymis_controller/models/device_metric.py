import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_serializer

__all__ = [
    "DeviceMetricPoint",
    "MetricGranularity",
    "FleetDeviceMetric",
]


class MetricGranularity(str, Enum):
    one_min = "1min"
    fifteen_min = "15min"
    one_hour = "1h"
    six_hour = "6h"
    one_day = "1d"

    @staticmethod
    def to_seconds(granularity: "MetricGranularity") -> int:
        if granularity == MetricGranularity.one_min:
            return 60
        elif granularity == MetricGranularity.fifteen_min:
            return 15 * 60
        elif granularity == MetricGranularity.one_hour:
            return 60 * 60
        elif granularity == MetricGranularity.six_hour:
            return 6 * 60 * 60
        elif granularity == MetricGranularity.one_day:
            return 24 * 60 * 60
        else:
            raise ValueError(f"Unknown granularity: {granularity!r}")


class DeviceMetricPoint(BaseModel):
    timestamp: datetime
    cpu_percent: float
    ram_percent: float
    disk_percent: float

    @field_serializer("timestamp")
    def _ser_dt(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            # treat stored naive values as UTC, matching the rest of the project
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")


class FleetDeviceMetric(BaseModel):
    deployment_info_id: uuid.UUID
    name: Optional[str] = None
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    timestamp: datetime

    @field_serializer("timestamp")
    def _ser_dt(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
