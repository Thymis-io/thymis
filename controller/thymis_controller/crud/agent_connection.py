import logging
import uuid
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session
from thymis_controller import db_models, models

logger = logging.getLogger(__name__)


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
