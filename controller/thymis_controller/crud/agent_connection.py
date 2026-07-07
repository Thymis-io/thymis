import logging
import uuid
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select, text
from sqlalchemy.orm import Session
from thymis_controller import db_models, models

logger = logging.getLogger(__name__)


def _aware(dt):
    return dt.replace(tzinfo=timezone.utc) if dt and dt.tzinfo is None else dt


def create(
    db_session: Session,
    connection_type: Literal["connect", "disconnect"],
    deployment_info_id: uuid.UUID,
):
    open_connection = (
        db_session.query(db_models.AgentConnection)
        .filter(
            db_models.AgentConnection.deployment_info_id == deployment_info_id,
            db_models.AgentConnection.disconnected_at.is_(None),
        )
        .first()
    )

    if connection_type == "connect":
        if open_connection:
            logger.warning(
                f"Connect requested but an open connection already exists for deployment_info_id: {deployment_info_id}. Closing previous one."
            )
            open_connection.disconnected_at = datetime.now(timezone.utc)
        db_session.add(
            db_models.AgentConnection(
                connected_at=datetime.now(timezone.utc),
                deployment_info_id=deployment_info_id,
            )
        )
    elif connection_type == "disconnect":
        if open_connection:
            open_connection.disconnected_at = datetime.now(timezone.utc)
        else:
            logger.warning(
                f"Disconnect requested but no open connection found for deployment_info_id: {deployment_info_id}"
            )

    db_session.commit()


def get_all_connected(
    db_session: Session,
) -> list[db_models.AgentConnection]:
    return (
        db_session.query(db_models.AgentConnection)
        .filter(db_models.AgentConnection.disconnected_at.is_(None))
        .all()
    )


def get_max_concurrent_connections(
    db_session: Session,
    range_from: datetime,
    range_to: datetime,
) -> list[models.AgentConnection]:
    stmt = text(
        """
        WITH base_timestamps AS (
            SELECT connected_at AS ts FROM agent_connections
            UNION
            SELECT disconnected_at FROM agent_connections WHERE disconnected_at IS NOT NULL
            UNION
            SELECT :range_from
            UNION
            SELECT :range_to
        ),
        filtered_timestamps AS (
            SELECT ts
            FROM base_timestamps
            WHERE ts >= :range_from AND ts < :range_to
        ),
        concurrent_sets AS (
            SELECT
                ts,
                ac.id,
                ac.deployment_info_id,
                ac.connected_at,
                ac.disconnected_at
            FROM filtered_timestamps ts
            JOIN agent_connections ac
            ON ac.connected_at <= ts.ts
            AND (ac.disconnected_at IS NULL OR ac.disconnected_at > ts.ts)
        ),
        concurrent_counts AS (
            SELECT ts, COUNT(*) AS cnt
            FROM concurrent_sets
            GROUP BY ts
        ),
        max_ts AS (
            SELECT ts
            FROM concurrent_counts
            ORDER BY cnt DESC, ts
            LIMIT 1
        )
        SELECT id, deployment_info_id, connected_at, disconnected_at
        FROM concurrent_sets
        WHERE ts = (SELECT ts FROM max_ts)
        ORDER BY deployment_info_id;
        """
    )

    values = {
        "range_from": range_from,
        "range_to": range_to,
    }
    result = db_session.execute(stmt, values).fetchall()

    deployment_info_ids = list({uuid.UUID(row.deployment_info_id) for row in result})
    deployment_info_map = {
        deployment_info.id: deployment_info
        for deployment_info in db_session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.id.in_(deployment_info_ids))
        .all()
    }

    return [
        models.AgentConnection(
            id=row.id,
            connected_at=row.connected_at,
            disconnected_at=row.disconnected_at,
            deployment_info=models.DeploymentInfo.from_deployment_info(
                deployment_info_map[uuid.UUID(row.deployment_info_id)]
            ),
        )
        for row in result
    ]


def get_by_deployment_info(
    db_session: Session,
    deployment_info_id: uuid.UUID,
    limit: int,
) -> list[db_models.AgentConnection]:
    """Return the most recent N connections for a device."""
    return (
        db_session.query(db_models.AgentConnection)
        .filter(db_models.AgentConnection.deployment_info_id == deployment_info_id)
        .order_by(db_models.AgentConnection.connected_at.desc())
        .limit(limit)
        .all()
    )


def get_availability_matrix(
    db_session: Session,
    from_datetime: datetime,
    to_datetime: datetime,
    buckets: int,
) -> models.FleetAvailability:
    """Per-device online/offline state sampled at evenly spaced points."""
    buckets = max(1, buckets)
    span = (to_datetime - from_datetime) / buckets
    sample_points = [from_datetime + span * i for i in range(buckets + 1)]

    conns = (
        db_session.query(db_models.AgentConnection)
        .filter(
            db_models.AgentConnection.connected_at <= to_datetime,
            (db_models.AgentConnection.disconnected_at.is_(None))
            | (db_models.AgentConnection.disconnected_at >= from_datetime),
        )
        .all()
    )

    # Pre-normalise each connection to a timezone-aware (connected, disconnected)
    # interval once, so the per-sample-point loop below stays cheap and readable.
    by_device: dict[uuid.UUID, list[tuple[datetime, datetime | None]]] = {}
    for c in conns:
        by_device.setdefault(c.deployment_info_id, []).append(
            (_aware(c.connected_at), _aware(c.disconnected_at))
        )

    # Get all devices in the system, not just ones with connections in the time window.
    all_devices = (
        db_session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.archived.is_(False))
        .all()
    )
    names = {di.id: di.name for di in all_devices}

    for device in all_devices:
        if device.id not in by_device:
            by_device[device.id] = []

    rows: list[models.DeviceAvailabilityRow] = []
    for di_id, intervals in by_device.items():
        if di_id not in names:
            continue
        states: list[bool] = []
        for t in sample_points:
            online = any(
                connected_at <= t and (disconnected_at is None or disconnected_at > t)
                for connected_at, disconnected_at in intervals
            )
            states.append(online)
        rows.append(
            models.DeviceAvailabilityRow(
                deployment_info_id=di_id,
                name=names.get(di_id),
                states=states,
            )
        )

    rows.sort(key=lambda r: (r.name or str(r.deployment_info_id)))
    return models.FleetAvailability(timestamps=sample_points, devices=rows)


def get_connectivity_series(
    db_session: Session,
    from_datetime: datetime,
    to_datetime: datetime,
    buckets: int,
) -> list[models.ConnectivityPoint]:
    """Return the count of connected devices sampled at evenly spaced points."""
    buckets = max(1, buckets)
    span = (to_datetime - from_datetime) / buckets
    sample_points = [from_datetime + span * i for i in range(buckets + 1)]

    conns = db_session.execute(
        select(
            db_models.AgentConnection.connected_at,
            db_models.AgentConnection.disconnected_at,
        ).where(
            db_models.AgentConnection.connected_at <= to_datetime,
            (db_models.AgentConnection.disconnected_at.is_(None))
            | (db_models.AgentConnection.disconnected_at >= from_datetime),
        )
    ).all()

    events: list[tuple[datetime, int]] = []
    for connected_at, disconnected_at in conns:
        events.append((_aware(connected_at), +1))
        if disconnected_at is not None:
            events.append((_aware(disconnected_at), -1))
    events.sort()

    active_count = 0
    event_idx = 0
    points: list[models.ConnectivityPoint] = []
    for t in sample_points:
        while event_idx < len(events):
            event_time, delta = events[event_idx]
            if event_time > t:
                break
            active_count += delta
            event_idx += 1
        points.append(
            models.ConnectivityPoint(timestamp=t, connected_count=active_count)
        )
    return points
