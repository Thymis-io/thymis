import logging

from fastapi import APIRouter, HTTPException
from thymis_controller.crud.external_repositories import (
    get_head_commit,
    get_repo_branches,
    get_repo_tags,
)
from thymis_controller.dependencies import DBSessionAD, ProjectAD
from thymis_controller.models.external_repo import (
    GitFlakeReference,
    GithubFlakeReference,
)
from thymis_controller.nix import nix_flake_prefetch
from thymis_controller.nix.flake_reference import parse_flake_reference

logger = logging.getLogger(__name__)

router = APIRouter(tags=["External Repositories"])


@router.get("/external-repositories/status")
def get_external_repositories_status(project: ProjectAD):
    return project.external_repo_status


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
            if not head_commit or head_commit.get("sha") is None:
                return {"status": "error", "detail": "Could not fetch head commit"}
        except HTTPException as e:
            return {"status": "error", "detail": str(e)}

    prefetch_success, prefetch_error = nix_flake_prefetch(flake.url, api_key)
    if not prefetch_success:
        return {"status": "error", "detail": prefetch_error}

    return {"status": "success"}


@router.get("/external-repositories/branches/{flake_name}")
async def get_flake_branches(flake_name: str, project: ProjectAD, session: DBSessionAD):
    flake = project.read_state().repositories.get(flake_name)
    if not flake:
        raise HTTPException(status_code=404, detail="Flake not found")
    api_key = project.get_secret(session, flake.api_key_secret)
    flake_ref = parse_flake_reference(flake.url)

    if isinstance(flake_ref, (GitFlakeReference, GithubFlakeReference)):
        return await get_repo_branches(flake_ref, api_key)
    return []


@router.get("/external-repositories/tags/{flake_name}")
async def get_flake_tags(flake_name: str, project: ProjectAD, session: DBSessionAD):
    flake = project.read_state().repositories.get(flake_name)
    if not flake:
        raise HTTPException(status_code=404, detail="Flake not found")
    api_key = project.get_secret(session, flake.api_key_secret)
    flake_ref = parse_flake_reference(flake.url)

    if isinstance(flake_ref, (GitFlakeReference, GithubFlakeReference)):
        return await get_repo_tags(flake_ref, api_key)
    return []
