from sqlalchemy.orm import Session
from thymis_controller import db_models


def create(
    db_session: Session,
    identifier: str,
    build_hash: str,
    device_state: dict,
    commit_hash: str,
):
    image = db_models.Image(
        identifier=identifier,
        build_hash=build_hash,
        device_state=device_state,
        commit_hash=commit_hash,
        valid=True,
    )
    db_session.add(image)
    db_session.commit()
    return image


def get_by_build_hash(db_session: Session, build_hash: str):
    # currently only the latest image of a build hash is returned
    return (
        db_session.query(db_models.Image)
        .filter(db_models.Image.build_hash == build_hash)
        .order_by(db_models.Image.created_at.desc())
        .first()
    )
