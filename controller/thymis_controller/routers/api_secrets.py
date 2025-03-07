import base64
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from thymis_controller.dependencies import DBSessionAD, ProjectAD
from thymis_controller.models.secrets import SecretCreateRequest, SecretShort

router = APIRouter()


@router.get("/secrets")
async def get_secrets(
    session: DBSessionAD, project: ProjectAD
) -> dict[uuid.UUID, SecretShort]:
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

    # Pass include_in_image and processing_type to create_secret
    return project.create_secret(
        session,
        secret_create.display_name,
        secret_create.type,
        value,
        secret_create.filename,
        include_in_image=secret_create.include_in_image,
        processing_type=secret_create.processing_type,
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
    if secret_update.value_str is not None:
        value = secret_update.value_str.encode("utf-8")

    # Pass include_in_image and processing_type to update_secret
    return project.update_secret(
        session,
        uuid.UUID(secret_id),
        secret_update.display_name,
        secret_update.type,
        value,
        secret_update.filename,
        include_in_image=secret_update.include_in_image,
        processing_type=secret_update.processing_type,
    )


@router.get("/secrets/{secret_id}/download")
async def download_secret(
    secret_id: uuid.UUID, session: DBSessionAD, project: ProjectAD
):
    # Try to download the file directly - add apply_processing=True
    res = project.download_secret_file(session, secret_id, apply_processing=True)
    if not res:
        raise HTTPException(status_code=404, detail="Secret not found")
    content, filename = res
    return Response(
        content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/secrets/{secret_id}")
async def delete_secret(
    secret_id: str, session: DBSessionAD, project: ProjectAD
) -> None:
    project.delete_secret(session, uuid.UUID(secret_id))
    return None
