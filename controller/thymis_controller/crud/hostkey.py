import datetime

from sqlalchemy.orm import Session
from thymis_controller import db_models
from thymis_controller.project import Project


def create(
    db_session: Session,
    identifier: str,
    build_hash: str,
    public_key: str,
    device_host: str,
    project: Project,
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

    # update known hosts
    project.update_known_hosts(db_session)

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
    # order by created_at as a workaround, paramiko only matches the first key (unlike OpenSSH)
    return (
        db_session.query(db_models.HostKey)
        .order_by(db_models.HostKey.created_at.desc())
        .all()
    )


def get_device_host(db_session: Session, identifier: str):
    device = (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.identifier == identifier)
        .first()
    )
    return device and device.device_host or None


def get_by_public_key(db_session: Session, public_key: str):
    return (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.public_key == public_key)
        .first()
    )


def get_by_build_hash(db_session: Session, build_hash: str):
    return (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.build_hash == build_hash)
        .order_by(db_models.HostKey.created_at.desc())
        .first()
    )


def rename_device(db_session: Session, old_identifier: str, new_identifier: str):
    device = (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.identifier == old_identifier)
        .first()
    )
    device.identifier = new_identifier
    db_session.commit()
    return device


def has_device(db_session: Session, identifier: str):
    return (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.identifier == identifier)
        .first()
    ) is not None


def get_by_identifier(db_session: Session, identifier: str):
    return (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.identifier == identifier)
        .first()
    )


def delete(db_session: Session, identifier: str):
    db_session.query(db_models.HostKey).where(
        db_models.HostKey.identifier == identifier
    ).delete()
    db_session.commit()
