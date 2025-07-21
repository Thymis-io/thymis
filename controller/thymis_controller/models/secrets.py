import logging
from datetime import datetime
from typing import Callable, Optional
from uuid import UUID

from pydantic import BaseModel
from pyrage import DecryptError
from thymis_controller import db_models

logger = logging.getLogger(__name__)


class SecretShort(BaseModel):
    id: UUID
    display_name: str
    type: db_models.SecretTypes
    value_str: Optional[str] = None
    value_size: int
    filename: Optional[str] = None
    include_in_image: bool
    processing_type: db_models.SecretProcessingTypes
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    delete_at: Optional[datetime] = None

    @classmethod
    def from_orm_secret(
        cls, secret: db_models.Secret, decryption_fn: Callable[[bytes], bytes]
    ) -> "SecretShort":
        error = None
        # only include value if type is not file
        if secret.type != db_models.SecretTypes.FILE:
            try:
                value_str = decryption_fn(secret.value_enc).decode("utf-8")
            except DecryptError as e:
                logger.error(
                    "Failed to decrypt secret %s (%s): %s",
                    secret.id,
                    secret.display_name,
                    e,
                )
                error = "Failed to decrypt secret: " + str(e)
                value_str = None
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
            error=error,
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


class SecretUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    type: Optional[db_models.SecretTypes] = None
    value_str: Optional[str] = None
    value_b64: Optional[str] = None
    filename: Optional[str] = None
    include_in_image: bool = False
    processing_type: Optional[db_models.SecretProcessingTypes] = None
