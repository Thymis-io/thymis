import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from thymis_controller import models
from thymis_controller.crud.artifacts import get_media_type
from thymis_controller.dependencies import ProjectAD
from thymis_controller.models.state import State

router = APIRouter()


def get_root_path(project: ProjectAD) -> Path:
    return project.repo_dir / "artifacts"


def validate_file_path(root: Path, file_name: str, should_exist: bool):
    path = (root / file_name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.parent == root.resolve():
        raise HTTPException(status_code=403, detail="Invalid path")
    if should_exist and not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if should_exist and not path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    return path


@router.get("/artifacts")
def get_artifacts(project: ProjectAD):
    root_path = get_root_path(project)

    if not root_path.exists():
        return []

    return [
        models.Artifact(
            name=path.name,
            media_type=get_media_type(path),
            size=path.stat().st_size,
            created_at=path.stat().st_ctime,
            modified_at=path.stat().st_mtime,
        )
        for path in sorted(root_path.iterdir(), key=lambda e: (e.is_file(), e.name))
        if path.is_file()
    ]


@router.get("/artifacts/{location}")
def get_artifact(location: str, project: ProjectAD):
    path = validate_file_path(get_root_path(project), location, should_exist=True)
    return Response(content=path.read_bytes(), media_type=get_media_type(path))


@router.post("/artifacts/")
def create_artifact(files: list[UploadFile], project: ProjectAD):
    for file in files:
        path = validate_file_path(
            get_root_path(project), file.filename, should_exist=False
        )
        os.makedirs(path.parent, exist_ok=True)
        with open(path, "wb") as f:
            f.write(file.file.read())
    return {"message": "Artifacts created"}


@router.delete("/artifacts/{location}")
def delete_artifact(location: str, project: ProjectAD):
    path = validate_file_path(get_root_path(project), location, should_exist=True)
    path.unlink()
    return {"message": "Artifact deleted"}


@router.post("/artifacts/rename/{location}")
def rename_artifact(location: str, new_name: str, project: ProjectAD):
    path = validate_file_path(get_root_path(project), location, should_exist=True)
    new_path = validate_file_path(get_root_path(project), new_name, should_exist=False)

    if new_path.exists():
        raise HTTPException(
            status_code=400, detail="Artifact with new name already exists"
        )

    path.rename(new_path)

    state = project.read_state()
    json = state.model_dump_json()
    json = json.replace(f'"artifact":"{location}"', f'"artifact":"{new_name}"')
    project.write_state(State.model_validate_json(json))

    return {"message": "Artifact renamed"}
