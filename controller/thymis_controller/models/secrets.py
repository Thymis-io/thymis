from datetime import datetime
from typing import Callable, Optional
from uuid import UUID

from pydantic import BaseModel
from thymis_controller import db_models


class SecretShort(BaseModel):
    id: UUID
    display_name: str
    type: db_models.SecretTypes
    value_str: Optional[str] = None
    value_size: int
    filename: Optional[str] = None
    include_in_image: bool
    processing_type: db_models.SecretProcessingTypes
    created_at: datetime
    updated_at: datetime
    delete_at: Optional[datetime] = None

    @classmethod
    def from_orm_secret(
        cls, secret: db_models.Secret, decryption_fn: Callable[[bytes], bytes]
    ) -> "SecretShort":
        # only include value if type is not file
        if secret.type != db_models.SecretTypes.FILE:
            value_str = decryption_fn(secret.value_enc).decode("utf-8")
        else:
            value_str = None
        return cls(
            id=secret.id,
            display_name=secret.display_name,
            type=secret.type,
            value_str=value_str,
            value_size=secret.value_size,
            filename=secret.filename,
            include_in_image=secret.include_in_image,
            processing_type=secret.processing_type,
            created_at=secret.created_at,
            updated_at=secret.updated_at,
            delete_at=secret.delete_at,
        )


class SecretCreateRequest(BaseModel):
    display_name: str
    type: db_models.SecretTypes
    value_str: Optional[str] = None
    value_b64: Optional[str] = None
    filename: Optional[str] = None
    include_in_image: bool = False
    processing_type: db_models.SecretProcessingTypes = (
        db_models.SecretProcessingTypes.NONE
    )
