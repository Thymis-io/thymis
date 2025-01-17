import operator
from functools import reduce

from sqlalchemy.orm import Session
from thymis_controller import db_models


def find_overlapping_hardware_ids(
    db_session: Session, hardware_ids: dict
) -> list[db_models.HardwareDevice]:
    # make a sqlalchemy json query
    return (
        db_session.query(db_models.HardwareDevice)
        .filter(
            reduce(
                operator.or_,
                (
                    (
                        db_models.HardwareDevice.hardware_ids.contains({key: value})
                        for key, value in hardware_ids.items()
                    )
                ),
            )
        )
        .all()
    )

    # for each hardware_id_key, hardware_id_value in hardware_ids.items():
    # WHERE hardware_ids[hardware_id_key] == hardware_id_value
    # CONNECTED WITH OR


def create(
    db_session: Session, hardware_ids: dict, deployment_info_id
) -> db_models.HardwareDevice:
    new_device = db_models.HardwareDevice(hardware_ids=hardware_ids)
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
        db_session.commit()
        db_session.refresh(overlapping_device)
        return overlapping_device
    return create(db_session, hardware_ids, deployment_info_id)
