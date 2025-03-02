import base64

from fastapi import APIRouter, HTTPException
from thymis_controller.dependencies import DBSessionAD, ProjectAD
from thymis_controller.models.secrets import SecretCreateRequest, SecretShort

router = APIRouter()


@router.get("/secrets")
async def get_secrets(session: DBSessionAD, project: ProjectAD) -> list[SecretShort]:
    return project.get_all_secrets(session)


@router.post("/secrets")
async def create_secret(
    secret_create: SecretCreateRequest, session: DBSessionAD, project: ProjectAD
) -> SecretShort:
    value = None
    if secret_create.value_b64:
        value = base64.b64decode(secret_create.value_b64)
    if secret_create.value_str:
        value = secret_create.value_str.encode("utf-8")
    if not value:
        raise HTTPException(
            status_code=400, detail="Either value_b64 or value_str must be provided"
        )
    return project.create_secret(
        session,
        secret_create.display_name,
        secret_create.type,
        value,
        secret_create.filename,
    )


@router.patch("/secrets/{secret_id}")
async def update_secret(
    secret_id: str,
    secret_update: SecretCreateRequest,
    session: DBSessionAD,
    project: ProjectAD,
) -> SecretShort:
    value = None
    if secret_update.value_b64:
        value = base64.b64decode(secret_update.value_b64)
    if secret_update.value_str:
        value = secret_update.value_str.encode("utf-8")
    if not value:
        raise HTTPException(
            status_code=400, detail="Either value_b64 or value_str must be provided"
        )
    return project.update_secret(
        session,
        secret_id,
        secret_update.display_name,
        secret_update.type,
        value,
        secret_update.filename,
    )
