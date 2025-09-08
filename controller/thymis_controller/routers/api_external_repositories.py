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

router = APIRouter()


@router.get("/flake-ref/{flake_name}")
def parse_flake_url(flake_name: str, project: ProjectAD, session: DBSessionAD):
    flake = project.read_state().repositories.get(flake_name)
    if not flake:
        raise HTTPException(status_code=404, detail="Flake not found")
    api_key = project.get_secret(session, flake.api_key_secret)
    flake_ref = parse_flake_reference(flake.url)

    if isinstance(flake_ref, GitFlakeReference):
        try:
            flake_ref.branches = get_repo_branches(flake_ref, api_key)
        except HTTPException:
            pass

        try:
            flake_ref.head_commit = get_head_commit(flake_ref, api_key)
        except HTTPException as e:
            logger.error(f"Error fetching branches: {e.detail}")

    return flake_ref
