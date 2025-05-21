import subprocess

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from thymis_controller import models
from thymis_controller.dependencies import ProjectAD

router = APIRouter()


@router.get("/artifacts")
def get_artifacts(project: ProjectAD):
    root_path = project.repo_dir / "artifacts"
    if not root_path.exists():
        return []

    result = []
    stack = [(root_path, result)]

    while stack:
        current_path, current_children = stack.pop()
        entries = sorted(current_path.iterdir(), key=lambda e: (e.is_file(), e.name))

        for entry in entries:
            relative_path = entry.relative_to(root_path)
            if entry.is_dir():
                folder = models.Folder(
                    name=entry.name, path=str(relative_path), children=[]
                )
                current_children.append(folder)
                stack.append((entry, folder.children))
            else:
                file = models.File(name=entry.name, path=str(relative_path))
                current_children.append(file)

    return result


@router.get("/artifacts/{location:path}")
def get_artifact(location: str, project: ProjectAD):
    path = project.repo_dir / "artifacts" / location

    if not path.is_relative_to(project.repo_dir / "artifacts"):
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


@router.post("/artifacts/upload/{location:path}")
def create_artifact(location: str, files: list[UploadFile], project: ProjectAD):
    path = project.repo_dir / "artifacts" / location

    if not path.is_relative_to(project.repo_dir / "artifacts"):
        raise HTTPException(status_code=403, detail="Invalid path")

    path.mkdir(parents=True, exist_ok=True)
    for file in files:
        with open(path / file.filename, "wb") as f:
            f.write(file.file.read())

    return {"message": "Artifact created"}


@router.delete("/artifacts/{location:path}")
def delete_artifact(location: str, project: ProjectAD):
    path = project.repo_dir / "artifacts" / location

    if not path.is_relative_to(project.repo_dir / "artifacts"):
        raise HTTPException(status_code=403, detail="Invalid path")

    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    if path.is_dir():
        for child in path.rglob("*"):
            child.unlink()
        path.rmdir()
    else:
        path.unlink()

    return {"message": "Artifact deleted"}


class MoveArtifact(BaseModel):
    artifact: str


# move an artifact to a folder
@router.post("/artifacts/move/{location:path}")
def move_artifact(location: str, move: MoveArtifact, project: ProjectAD):
    src = project.repo_dir / "artifacts" / move.artifact
    dst = project.repo_dir / "artifacts" / location

    while dst.exists() and dst.is_file():
        dst = dst.parent

    print(src, dst)

    if not src.is_relative_to(project.repo_dir / "artifacts") or not dst.is_relative_to(
        project.repo_dir / "artifacts"
    ):
        raise HTTPException(status_code=403, detail="Invalid path")

    if not src.exists():
        raise HTTPException(status_code=404, detail="Source artifact not found")

    if src == dst:
        raise HTTPException(
            status_code=400, detail="Source and destination are the same"
        )

    if src in dst.parents:
        raise HTTPException(
            status_code=400, detail="Destination cannot be a subfolder of source"
        )

    src.rename(dst / src.name)

    return {"message": "Artifact moved"}
