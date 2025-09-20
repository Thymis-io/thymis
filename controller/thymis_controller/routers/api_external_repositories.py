import logging

from fastapi import APIRouter, HTTPException
from thymis_controller.crud.external_repositories import (
    GitFlakeReference,
    get_head_commit,
    get_repo_branches,
    parse_flake_reference,
)
from thymis_controller.dependencies import DBSessionAD, ProjectAD

logger = logging.getLogger(__name__)

router = APIRouter(tags=["External Repositories"])


@router.get("/external-repositories/flake-ref/{flake_name}")
def parse_flake_url(flake_name: str, project: ProjectAD):
    flake = project.read_state().repositories.get(flake_name)
    if not flake:
        raise HTTPException(status_code=404, detail="Flake not found")
    return parse_flake_reference(flake.url)


@router.get("/external-repositories/test-flake-ref/{flake_name}")
async def test_fake_reference(
    flake_name: str, project: ProjectAD, session: DBSessionAD
):
    flake = project.read_state().repositories.get(flake_name)
    if not flake:
        raise HTTPException(status_code=404, detail="Flake not found")
    api_key = project.get_secret(session, flake.api_key_secret)
    flake_ref = parse_flake_reference(flake.url)

    if isinstance(flake_ref, GitFlakeReference):
        try:
            head_commit = await get_head_commit(flake_ref, api_key)
            if head_commit and head_commit.get("sha") is not None:
                return {"status": "success"}
        except HTTPException as e:
            if e.status_code == 403 or e.status_code == 429:
                return {"status": "rate_limited"}
            try:
                message = (
                    e.detail.get("message", {}).get("message", "")
                    if isinstance(e.detail, dict)
                    else ""
                )
            except Exception:
                message = str(e.detail)
            return {"status": "error", "detail": f"{e.status_code} {message}"}
    return {"status": "unknown"}


@router.get("/external-repositories/branches/{flake_name}")
async def get_flake_branches(flake_name: str, project: ProjectAD, session: DBSessionAD):
    flake = project.read_state().repositories.get(flake_name)
    if not flake:
        raise HTTPException(status_code=404, detail="Flake not found")
    api_key = project.get_secret(session, flake.api_key_secret)
    flake_ref = parse_flake_reference(flake.url)

    if isinstance(flake_ref, GitFlakeReference):
        try:
            branches = await get_repo_branches(flake_ref, api_key)
            if branches:
                return branches
        except HTTPException as e:
            if e.status_code == 403 or e.status_code == 429:
                raise HTTPException(status_code=503, detail="Rate limited")
            try:
                message = (
                    e.detail.get("message", {}).get("message", "")
                    if isinstance(e.detail, dict)
                    else ""
                )
            except Exception:
                message = str(e.detail)
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching branches: {e.status_code} {message}",
            )
    raise HTTPException(status_code=400, detail="Not a git-based flake URL")
