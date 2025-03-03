import uuid
from datetime import datetime, timezone

import thymis_controller.db_models as db_models
from sqlalchemy.orm import Session

# import enum
# import uuid
# from datetime import datetime, timezone
# from sqlalchemy import Column, Text, LargeBinary, DateTime, ForeignKey, Enum
# from sqlalchemy.dialects.postgresql import UUID

# from thymis_controller.database.base import Base

# class SecretTypes(enum.Enum):
#     SINGLE_LINE = "single_line"
#     MULTI_LINE = "multi_line"
#     ENV_LIST = "env_list"
#     FILE = "file"

# class Secret(Base):
#     __tablename__ = "secrets"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     display_name = Column(Text, nullable=False)
#     type = Column(Enum(SecretTypes), nullable=False)
#     value = Column(LargeBinary, nullable=False)
#     filename = Column(Text, nullable=True)
#     created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
#     updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

#     delete_at = Column(DateTime(timezone=True), nullable=True)


def create(
    db_session: Session,
    display_name: str,
    secret_type: db_models.SecretTypes,
    value_enc: bytes,
    value_size: int,
    filename: str | None = None,
) -> db_models.Secret:
    new_secret = db_models.Secret(
        id=uuid.uuid4(),
        display_name=display_name,
        type=secret_type,
        value_enc=value_enc,
        value_size=value_size,
        filename=filename,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(new_secret)
    db_session.commit()
    db_session.refresh(new_secret)
    return new_secret


def get_all_secrets(db_session: Session) -> list[db_models.Secret]:
    # return db_session.query(db_models.Secret).all()
    return db_session.query(db_models.Secret).filter_by(delete_at=None).all()


def get_by_id(db_session: Session, secret_id: uuid.UUID) -> db_models.Secret | None:
    # return db_session.query(db_models.Secret).filter_by(id=secret_id).first()
    return (
        db_session.query(db_models.Secret)
        .filter_by(id=secret_id, delete_at=None)
        .first()
    )


def update(
    db_session: Session,
    secret_id: uuid.UUID,
    display_name: str | None = None,
    secret_type: db_models.SecretTypes | None = None,
    value_enc: bytes | None = None,
    value_size: int | None = None,
    filename: str | None = None,
) -> db_models.Secret | None:
    secret = get_by_id(db_session, secret_id)
    if not secret:
        return None

    if display_name:
        secret.display_name = display_name
    if secret_type:
        secret.type = secret_type
    if value_enc:
        secret.value_enc = value_enc
    if value_size:
        secret.value_size = value_size
    if filename:
        secret.filename = filename
    secret.updated_at = datetime.now(timezone.utc)

    db_session.commit()
    db_session.refresh(secret)
    return secret


def delete(db_session: Session, secret_id: uuid.UUID) -> bool:
    secret = get_by_id(db_session, secret_id)
    if not secret:
        return False
    # mark as deleted
    secret.delete_at = datetime.now(timezone.utc)
    db_session.commit()
    return True
