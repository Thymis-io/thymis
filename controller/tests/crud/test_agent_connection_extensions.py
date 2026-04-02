import uuid
from datetime import datetime, timezone

from thymis_controller import db_models
from thymis_controller.crud import agent_connection as crud


def _make_di(db_session):
    di = db_models.DeploymentInfo(
        ssh_public_key=f"ssh-ed25519 AAAA{uuid.uuid4().hex}",
        deployed_config_id="cfg",
    )
    db_session.add(di)
    db_session.commit()
    db_session.refresh(di)
    return di


def test_get_by_deployment_info_returns_last_10(db_session):
    di = _make_di(db_session)
    # Create 15 connections
    for i in range(15):
        conn = db_models.AgentConnection(
            deployment_info_id=di.id,
            connected_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
        )
        db_session.add(conn)
    db_session.commit()

    results = crud.get_by_deployment_info(db_session, di.id)
    assert len(results) == 10
    # Most recent first
    assert results[0].connected_at > results[-1].connected_at
