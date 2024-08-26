import datetime

from sqlalchemy.orm import Session
from thymis_controller import db_models


def create_or_update(db_session: Session, identifier: str, build_hash: str):
    hostkey = (
        db_session.query(db_models.HostKey).filter_by(identifier=identifier).first()
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
