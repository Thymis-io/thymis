from typing import Optional

import httpx
from cachetools import TTLCache
from fastapi import HTTPException
from thymis_controller.asyncache import cached
from thymis_controller.models.external_repo import (
    FlakeReference,
    GitFlakeReference,
    GithubFlakeReference,
    GitlabFlakeReference,
)
from thymis_controller.models.secrets import SecretShort


async def _request_json(url: str, api_key: Optional["SecretShort"]):
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key.value_str}"

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()

    raise HTTPException(
        status_code=response.status_code,
        detail=response.json(),
    )


@cached(
    cache=TTLCache(maxsize=100, ttl=60),
    key=lambda owner, repo, api_key: f"{owner}/{repo}/{api_key.id if api_key else 'no_key'}",
)
async def _get_github_branches(owner: str, repo: str, api_key: Optional["SecretShort"]):
    return await _request_json(
        f"https://api.github.com/repos/{owner}/{repo}/branches", api_key
    )


@cached(
    cache=TTLCache(maxsize=100, ttl=60),
    key=lambda owner, repo, api_key: f"{owner}/{repo}/{api_key.id if api_key else 'no_key'}",
)
async def _get_github_tags(owner: str, repo: str, api_key: Optional["SecretShort"]):
    return await _request_json(
        f"https://api.github.com/repos/{owner}/{repo}/tags", api_key
    )


@cached(
    cache=TTLCache(maxsize=100, ttl=60),
    key=lambda owner, repo, ref, rev, api_key: f"{owner}/{repo}/{ref or rev or 'HEAD'}/{api_key.id if api_key else 'no_key'}",
)
async def _get_github_get_head_commit(
    owner: str, repo: str, ref: str, rev: str, api_key: Optional["SecretShort"]
):
    return await _request_json(
        f"https://api.github.com/repos/{owner}/{repo}/commits/{ref or rev or 'HEAD'}",
        api_key,
    )


@cached(
    cache=TTLCache(maxsize=100, ttl=60),
    key=lambda owner, repo, api_key: f"{owner}/{repo}/{api_key.id if api_key else 'no_key'}",
)
def _get_gitlab_branches(owner: str, repo: str, api_key: Optional["SecretShort"]):
    project_path = f"{owner}/{repo}".replace("/", "%2F")
    return _request_json(
        f"https://gitlab.com/api/v4/projects/{project_path}/repository/branches",
        api_key,
    )


@cached(
    cache=TTLCache(maxsize=100, ttl=60),
    key=lambda owner, repo, api_key: f"{owner}/{repo}/{api_key.id if api_key else 'no_key'}",
)
def _get_gitlab_tags(owner: str, repo: str, api_key: Optional["SecretShort"]):
    project_path = f"{owner}/{repo}".replace("/", "%2F")
    return _request_json(
        f"https://gitlab.com/api/v4/projects/{project_path}/repository/tags",
        api_key,
    )


@cached(
    cache=TTLCache(maxsize=100, ttl=60),
    key=lambda owner, repo, ref, rev, api_key: f"{owner}/{repo}/{ref or rev or 'HEAD'}/{api_key.id if api_key else 'no_key'}",
)
async def _get_gitlab_get_head_commit(
    owner: str, repo: str, ref: str, rev: str, api_key: Optional["SecretShort"]
):
    project_path = f"{owner}/{repo}".replace("/", "%2F")
    return await _request_json(
        f"https://gitlab.com/api/v4/projects/{project_path}/repository/commits/{ref or rev or 'HEAD'}",
        api_key,
    )


def is_github(reference: FlakeReference) -> bool:
    if isinstance(reference, GithubFlakeReference):
        return True
    if isinstance(reference, GitFlakeReference) and reference.host == "github.com":
        return True
    return False


def is_gitlab(reference: FlakeReference) -> bool:
    if isinstance(reference, GitlabFlakeReference):
        return True
    if isinstance(reference, GitFlakeReference) and reference.host == "gitlab.com":
        return True
    return False


async def get_repo_branches(reference: FlakeReference, api_key: Optional[SecretShort]):
    if is_github(reference):
        return await _get_github_branches(reference.owner, reference.repo, api_key)
    if is_gitlab(reference):
        return await _get_gitlab_branches(reference.owner, reference.repo, api_key)
    return []


async def get_repo_tags(reference: FlakeReference, api_key: Optional[SecretShort]):
    if is_github(reference):
        return await _get_github_tags(reference.owner, reference.repo, api_key)
    if is_gitlab(reference):
        return await _get_gitlab_tags(reference.owner, reference.repo, api_key)
    return []


async def get_head_commit(reference: FlakeReference, api_key: Optional[SecretShort]):
    if is_github(reference):
        commit = await _get_github_get_head_commit(
            reference.owner, reference.repo, reference.ref, reference.rev, api_key
        )
        return commit.get("sha") if commit else None
    if is_gitlab(reference):
        commit = await _get_gitlab_get_head_commit(
            reference.owner, reference.repo, reference.ref, reference.rev, api_key
        )
        return commit.get("id") if commit else None
    return None
