import pathlib
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from thymis_controller.config import global_settings

router = APIRouter()

_SAFE_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]*")


@router.get("/image-updates/{configuration_id}/{filename}")
def get_image_update(configuration_id: str, filename: str) -> FileResponse:
    if not _SAFE_COMPONENT.fullmatch(configuration_id) or not _SAFE_COMPONENT.fullmatch(
        filename
    ):
        raise HTTPException(status_code=404)

    update_root = (global_settings.PROJECT_PATH / "image-updates").resolve()
    artifact = (update_root / configuration_id / filename).resolve()
    if artifact.parent != update_root / configuration_id or not artifact.is_file():
        raise HTTPException(status_code=404)

    cache_control = (
        "no-store"
        if filename in {"SHA256SUMS", "SHA256SUMS.gpg"}
        else "public, max-age=31536000, immutable"
    )
    return FileResponse(
        pathlib.Path(artifact),
        headers={"Cache-Control": cache_control},
        media_type="application/octet-stream",
    )
