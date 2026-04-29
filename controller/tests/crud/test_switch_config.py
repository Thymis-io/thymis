"""
Integration tests for the switch-config / pending_config_id feature.

Invariants under test:
1. update() with pending_config_id sets the field.
2. update() with pending_config_id=None clears it without touching deployed_config_id.
3. create_or_update_by_public_key() does NOT auto-promote pending_config_id;
   the device-reported deployed_config_id always wins on reconnect.
4. Full switch round-trip:
   - switch-config sets pending_config_id
   - device reconnects reporting old id  → deployed_config_id stays old, pending intact
   - activation promotes deployed_config_id to the target and clears pending_config_id
   - the immediate reconnect report cannot bounce a confirmed switch back
"""

import uuid
from datetime import datetime, timezone

from thymis_controller import crud, db_models


def make_deployment_info(
    db_session, ssh_public_key="key-a", deployed_config_id="config-a"
):
    di = db_models.DeploymentInfo(
        ssh_public_key=ssh_public_key,
        deployed_config_id=deployed_config_id,
    )
    db_session.add(di)
    db_session.commit()
    db_session.refresh(di)
    return di


def make_completed_switch_task(
    db_session, deployment_info_id, source_identifier, target_identifier
):
    task = db_models.Task(
        id=uuid.uuid4(),
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        state="completed",
        task_type="deploy_device_task",
        user_session_id=uuid.uuid4(),
        task_submission_data={
            "type": "deploy_device_task",
            "device": {
                "identifier": target_identifier,
                "source_identifier": source_identifier,
                "deployment_info_id": str(deployment_info_id),
                "deployment_public_key": "key-a",
                "secrets": [],
            },
        },
    )
    db_session.add(task)
    db_session.commit()
    return task


# ---------------------------------------------------------------------------
# 1. update() sets pending_config_id
# ---------------------------------------------------------------------------


def test_update_sets_pending_config_id(db_session):
    di = make_deployment_info(db_session)

    updated = crud.deployment_info.update(
        db_session, di.id, pending_config_id="config-b"
    )

    assert updated.pending_config_id == "config-b"
    # deployed_config_id must be untouched
    assert updated.deployed_config_id == "config-a"


# ---------------------------------------------------------------------------
# 2. update() with pending_config_id=None nulls the field without touching deployed
# ---------------------------------------------------------------------------


def test_clear_pending_config_id(db_session):
    di = make_deployment_info(db_session)
    crud.deployment_info.update(db_session, di.id, pending_config_id="config-b")

    updated = crud.deployment_info.update(db_session, di.id, pending_config_id=None)

    assert updated.pending_config_id is None
    assert updated.deployed_config_id == "config-a"


# ---------------------------------------------------------------------------
# 3. create_or_update_by_public_key does NOT auto-promote pending_config_id
# ---------------------------------------------------------------------------


def test_reconnect_does_not_promote_pending_config_id(db_session):
    di = make_deployment_info(db_session, deployed_config_id="config-a")
    # Simulate a pending switch to config-b
    crud.deployment_info.update(db_session, di.id, pending_config_id="config-b")

    # Device reconnects still reporting the old config (deploy hasn't landed yet)
    result = crud.deployment_info.create_or_update_by_public_key(
        db_session,
        ssh_public_key="key-a",
        deployed_config_id="config-a",
    )

    # deployed_config_id reflects what the device reported — config-a
    assert result.deployed_config_id == "config-a"
    # pending_config_id is untouched — still config-b
    assert result.pending_config_id == "config-b"


# ---------------------------------------------------------------------------
# 4. Full switch round-trip
# ---------------------------------------------------------------------------


def test_full_switch_round_trip(db_session):
    di = make_deployment_info(db_session, deployed_config_id="config-a")

    # Step 1: switch-config endpoint sets pending_config_id
    crud.deployment_info.update(db_session, di.id, pending_config_id="config-b")
    di_after_switch = crud.deployment_info.get_by_id(db_session, di.id)
    assert di_after_switch.pending_config_id == "config-b"
    assert di_after_switch.deployed_config_id == "config-a"

    # Step 2: device reconnects mid-deploy still reporting old config — pending preserved
    crud.deployment_info.create_or_update_by_public_key(
        db_session, ssh_public_key="key-a", deployed_config_id="config-a"
    )
    di_mid = crud.deployment_info.get_by_id(db_session, di.id)
    assert di_mid.deployed_config_id == "config-a"
    assert di_mid.pending_config_id == "config-b"

    # Step 3: deploy succeeds, is_activated=True — promote target config and clear pending
    crud.deployment_info.update(
        db_session,
        di.id,
        deployed_config_id="config-b",
        deployed_config_commit="abc123",
        pending_config_id=None,
    )
    di_activated = crud.deployment_info.get_by_id(db_session, di.id)
    assert di_activated.pending_config_id is None
    assert di_activated.deployed_config_commit == "abc123"
    assert di_activated.deployed_config_id == "config-b"

    make_completed_switch_task(db_session, di.id, "config-a", "config-b")

    # Step 4: the agent reconnect for the just-completed switch can still report
    # the source config until its local metadata has been updated. The
    # controller-confirmed switch target remains authoritative for that case.
    crud.deployment_info.create_or_update_by_public_key(
        db_session,
        ssh_public_key="key-a",
        deployed_config_id="config-a",
        preserve_confirmed_switch=True,
    )
    di_reconnected = crud.deployment_info.get_by_id(db_session, di.id)
    assert di_reconnected.deployed_config_id == "config-b"
    assert di_reconnected.pending_config_id is None

    # Step 5: device reconnects after activation reporting new config
    crud.deployment_info.create_or_update_by_public_key(
        db_session, ssh_public_key="key-a", deployed_config_id="config-b"
    )
    di_final = crud.deployment_info.get_by_id(db_session, di.id)
    assert di_final.deployed_config_id == "config-b"
    assert di_final.pending_config_id is None
