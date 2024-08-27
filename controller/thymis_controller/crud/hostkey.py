import datetime

from sqlalchemy.orm import Session
from thymis_controller import db_models
from thymis_controller.dependencies import get_project
from thymis_controller.project import Project


def create_or_update(db_session: Session, identifier: str, build_hash: str):
    hostkey = (
        db_session.query(db_models.HostKey)
        .where(db_models.HostKey.identifier == identifier)
        .first()
    )

    if hostkey is None:
        hostkey = db_models.HostKey(
            identifier=identifier,
            build_hash=build_hash,
        )
        db_session.add(hostkey)
    else:
        hostkey.created_at = datetime.datetime.now(datetime.timezone.utc)
        hostkey.build_hash = build_hash
        # TODO maybe delete the old public key

    db_session.commit()
    return hostkey


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
