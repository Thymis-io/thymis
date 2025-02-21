import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from thymis_controller import db_models


def find_overlapping_hardware_ids(
    db_session: Session, hardware_ids: dict
) -> list[db_models.HardwareDevice]:
    query = None
    for key, value in hardware_ids.items():
        query_key = db_session.query(db_models.HardwareDevice).filter(
            db_models.HardwareDevice.hardware_ids[key] == json.dumps(value)
        )

        if query is None:
            query = query_key
        else:
            query = query.union(query_key)
    if query is None:
        return []
    return query.all()


def create(
    db_session: Session, hardware_ids: dict, deployment_info_id
) -> db_models.HardwareDevice:
    new_device = db_models.HardwareDevice(
        hardware_ids=hardware_ids, last_seen=datetime.now(timezone.utc)
    )
    if deployment_info_id:
        new_device.deployment_info_id = deployment_info_id
    db_session.add(new_device)
    db_session.commit()
    db_session.refresh(new_device)
    return new_device


def create_or_update(
    db_session: Session, hardware_ids: dict, deployment_info_id
) -> db_models.HardwareDevice:
    overlapping_devices = find_overlapping_hardware_ids(db_session, hardware_ids)
    if len(overlapping_devices) >= 2:
        raise ValueError("Multiple devices with the same hardware ids")
    if len(overlapping_devices) == 1:
        overlapping_device = overlapping_devices[0]
        overlapping_device.deployment_info_id = deployment_info_id
        overlapping_device.last_seen = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(overlapping_device)
        device = overlapping_device
    else:
        device = create(db_session, hardware_ids, deployment_info_id)
    # now, disassociate the deployment_info_id from all other devices
    db_session.query(db_models.HardwareDevice).filter(
        db_models.HardwareDevice.id != device.id,
        db_models.HardwareDevice.deployment_info_id == deployment_info_id,
    ).update({"deployment_info_id": None})
    db_session.commit()
    return device


def get_all(db_session: Session) -> list[db_models.HardwareDevice]:
    return (
        db_session.query(db_models.HardwareDevice)
        .order_by(db_models.HardwareDevice.last_seen.desc())
        .all()
    )
