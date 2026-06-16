from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session
from thymis_controller import db_models, models
from thymis_controller.crud import device_metric as crud_device_metric

# Tunable thresholds — adjust here, not at call sites.
RESOURCE_WARNING = 80.0
RESOURCE_CRITICAL = 90.0
OFFLINE_HOURS = 24
# A device is flagged as flapping when it has MORE THAN this many connect events
# within FLAPPING_WINDOW_HOURS (strict greater-than).
FLAPPING_RECONNECTS_24H = 5
FLAPPING_WINDOW_HOURS = 24
METRIC_FRESHNESS_HOURS = 24


def _aware(dt):
    return dt.replace(tzinfo=timezone.utc) if dt and dt.tzinfo is None else dt


def get_fleet_alerts(db_session: Session) -> list[models.FleetAlert]:
    now = datetime.now(timezone.utc)
    alerts: list[models.FleetAlert] = []

    # 1. Prolonged offline
    offline_cutoff = now - timedelta(hours=OFFLINE_HOURS)
    stale = (
        db_session.query(db_models.DeploymentInfo)
        .filter(
            db_models.DeploymentInfo.last_seen.isnot(None),
            db_models.DeploymentInfo.last_seen < offline_cutoff,
        )
        .all()
    )
    for di in stale:
        hours = (now - _aware(di.last_seen)).total_seconds() / 3600
        alerts.append(
            models.FleetAlert(
                deployment_info_id=di.id,
                name=di.name,
                kind="offline",
                severity="critical" if hours >= OFFLINE_HOURS * 3 else "warning",
                detail=f"Offline for {hours / 24:.1f} days",
                value=hours,
            )
        )

    # 2. Flapping (frequent reconnects in last 24h)
    since = now - timedelta(hours=FLAPPING_WINDOW_HOURS)
    flap_rows = (
        db_session.query(
            db_models.AgentConnection.deployment_info_id,
            func.count(db_models.AgentConnection.id).label("cnt"),
        )
        .filter(db_models.AgentConnection.connected_at >= since)
        .group_by(db_models.AgentConnection.deployment_info_id)
        .having(func.count(db_models.AgentConnection.id) > FLAPPING_RECONNECTS_24H)
        .all()
    )
    if flap_rows:
        names = {
            di.id: di.name
            for di in db_session.query(db_models.DeploymentInfo)
            .filter(
                db_models.DeploymentInfo.id.in_(
                    [r.deployment_info_id for r in flap_rows]
                )
            )
            .all()
        }
        for row in flap_rows:
            alerts.append(
                models.FleetAlert(
                    deployment_info_id=row.deployment_info_id,
                    name=names.get(row.deployment_info_id),
                    kind="flapping",
                    severity="warning",
                    detail=f"{row.cnt} reconnects in 24h",
                    value=float(row.cnt),
                )
            )

    # 3. Resource spikes from the latest fresh metric per device
    freshness_cutoff = now - timedelta(hours=METRIC_FRESHNESS_HOURS)
    for metric in crud_device_metric.get_latest_per_device(db_session):
        if _aware(metric.timestamp) < freshness_cutoff:
            continue
        for kind, value in (
            ("cpu", metric.cpu_percent),
            ("ram", metric.ram_percent),
            ("disk", metric.disk_percent),
        ):
            if value >= RESOURCE_WARNING:
                alerts.append(
                    models.FleetAlert(
                        deployment_info_id=metric.deployment_info_id,
                        name=metric.name,
                        kind=kind,
                        severity="critical"
                        if value >= RESOURCE_CRITICAL
                        else "warning",
                        detail=f"{kind.upper()} at {value:.0f}%",
                        value=value,
                    )
                )

    severity_rank = {"critical": 0, "warning": 1}
    alerts.sort(
        key=lambda a: (severity_rank[a.severity], a.kind, str(a.deployment_info_id))
    )
    return alerts
