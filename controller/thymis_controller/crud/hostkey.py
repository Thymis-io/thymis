import datetime

from sqlalchemy.orm import Session
from thymis_controller import db_models
from thymis_controller.dependencies import get_project
from thymis_controller.project import Project


def create(
    db_session: Session,
    identifier: str,
    build_hash: str,
    public_key: str,
    device_host: str,
):
    host_key = db_models.HostKey(
        identifier=identifier,
        build_hash=build_hash,
        public_key=public_key,
        device_host=device_host,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(host_key)
    db_session.commit()
    return host_key


def build_hash_is_registered(db_session: Session, build_hash: str):
    return (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.build_hash == build_hash)
        .first()
    ) is not None


def register_device(
    db_session: Session,
    project: Project,
    build_hash: str,
    public_key: str,
    device_host: str,
) -> bool:
    device = (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.build_hash == build_hash)
        .first()
    )

    if not device:
        return False

    device.public_key = public_key
    device.device_host = device_host
    db_session.commit()

    # update known hosts
    project.update_known_hosts(db_session)

    return True


def get_all(db_session: Session):
    return db_session.query(db_models.HostKey).all()


def get_device_host(db_session: Session, identifier: str):
    device = (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.identifier == identifier)
        .first()
    )
    return device and device.device_host or None
