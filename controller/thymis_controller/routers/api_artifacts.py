import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from thymis_controller import models
from thymis_controller.dependencies import ProjectAD
from thymis_controller.models.state import State

router = APIRouter()


@router.get("/artifacts")
def get_artifacts(project: ProjectAD):
    root_path = project.repo_dir / "artifacts"

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


def get_media_type(path: Path) -> str | None:
    try:
        return (
            subprocess.run(
                ["file", "--mime-type", "--brief", path],
                stdout=subprocess.PIPE,
                check=True,
            )
            .stdout.strip()
            .decode("utf-8")
        )
    except subprocess.CalledProcessError:
        return None


@router.get("/artifacts/{location:path}")
def get_artifact(location: str, project: ProjectAD):
    path = project.repo_dir / "artifacts" / location

    if path.parent != project.repo_dir / "artifacts" or not path.is_file():
        raise HTTPException(status_code=403, detail="Invalid path")

    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    media_type = (
        subprocess.run(
            ["file", "--mime-type", "--brief", str(path)],
            stdout=subprocess.PIPE,
            check=True,
        )
        .stdout.strip()
        .decode("utf-8")
    )

    if path.is_file():
        return Response(content=path.read_bytes(), media_type=media_type)
    else:
        return Response(content=b"", media_type="folder")


@router.post("/artifacts/")
def create_artifact(files: list[UploadFile], project: ProjectAD):
    path = project.repo_dir / "artifacts"

    for file in files:
        with open(path / file.filename, "wb") as f:
            f.write(file.file.read())

    return {"message": "Artifacts created"}


@router.delete("/artifacts/{location:path}")
def delete_artifact(location: str, project: ProjectAD):
    path = project.repo_dir / "artifacts" / location

    if path.parent != project.repo_dir / "artifacts" or not path.is_file():
        raise HTTPException(status_code=403, detail="Invalid path")

    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    path.unlink()

    return {"message": "Artifact deleted"}


@router.post("/artifacts/rename/{location:path}")
def rename_artifact(location: str, new_name: str, project: ProjectAD):
    path = project.repo_dir / "artifacts" / location

    if path.parent != project.repo_dir / "artifacts" or not path.is_file():
        raise HTTPException(status_code=403, detail="Invalid path")

    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    new_path = path.parent / new_name
    if new_path.exists():
        raise HTTPException(
            status_code=400, detail="Artifact with new name already exists"
        )

    if new_path.parent != path.parent:
        raise HTTPException(
            status_code=403, detail="Cannot move artifact to another directory"
        )

    path.rename(new_path)

    state = project.read_state()
    json = state.model_dump_json()
    json = json.replace(f'"artifact":"{location}"', f'"artifact":"{new_name}"')
    project.write_state(State.model_validate_json(json))

    return {"message": "Artifact renamed"}
