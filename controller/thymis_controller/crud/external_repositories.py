from typing import Optional

import httpx
from cachetools import TTLCache
from fastapi import HTTPException
from thymis_controller.asyncache import cached
from thymis_controller.models.external_repo import (
    GitFlakeReference,
    GithubFlakeReference,
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


async def get_repo_branches(
    reference: GitFlakeReference | GithubFlakeReference, api_key: Optional[SecretShort]
):
    if isinstance(reference, GithubFlakeReference) or (
        reference.host and "github.com" in reference.host
    ):
        return await _get_github_branches(reference.owner, reference.repo, api_key)
    return []


async def get_repo_tags(
    reference: GitFlakeReference | GithubFlakeReference, api_key: Optional[SecretShort]
):
    if isinstance(reference, GithubFlakeReference) or (
        reference.host and "github.com" in reference.host
    ):
        return await _get_github_tags(reference.owner, reference.repo, api_key)
    return []


async def get_head_commit(
    reference: GitFlakeReference | GithubFlakeReference, api_key: Optional[SecretShort]
):
    if isinstance(reference, GithubFlakeReference) or (
        reference.host and "github.com" in reference.host
    ):
        return await _get_github_get_head_commit(
            reference.owner, reference.repo, reference.ref, reference.rev, api_key
        )
    return None
