from sqlalchemy.orm import Session
from thymis_controller import db_models


def get_by_hardware_id(
    db_session: Session, hardware_id: str
) -> db_models.HardwareDevice | None:
    return (
        db_session.query(db_models.HardwareDevice)
        .filter(db_models.HardwareDevice.hardware_id == hardware_id)
        .first()
    )


def create(
    db_session: Session, hardware_id: str, deployment_info_id
) -> db_models.HardwareDevice:
    new_device = db_models.HardwareDevice(hardware_id=hardware_id)
    if deployment_info_id:
        new_device.deployment_info_id = deployment_info_id
    db_session.add(new_device)
    db_session.commit()
    db_session.refresh(new_device)
    return new_device


def create_or_update(
    db_session: Session, hardware_id: str, deployment_info_id: str
) -> db_models.HardwareDevice:
    device = get_by_hardware_id(db_session, hardware_id)
    if device:
        device.deployment_info_id = deployment_info_id
        db_session.commit()
        db_session.refresh(device)
        return device
    return create(db_session, hardware_id, deployment_info_id)
