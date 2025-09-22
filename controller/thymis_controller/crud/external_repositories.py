from typing import Literal, Optional

import httpx
from cachetools import TTLCache
from fastapi import HTTPException
from pydantic import BaseModel
from thymis_controller.asyncache import cached
from thymis_controller.models.secrets import SecretShort


class FlakeReference(BaseModel):
    # https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-flake.html#types
    type: Literal[
        "indirect",
        "path",
        "git",
        "mercurial",
        "tarball",
        "file",
        "github",
        "gitlab",
        "sourcehut",
    ]


class IndirectFlakeReference(FlakeReference):
    type: Literal["indirect"]
    flake_id: str
    rev: str | None
    ref: str | None


class GitFlakeReference(FlakeReference):
    type: Literal["git"]
    protocol: Literal["http", "https", "ssh", "git", "file"]
    url: str
    host: str
    owner: str | None
    repo: str
    ref: str | None
    rev: str | None


class GithubFlakeReference(FlakeReference):
    type: Literal["github"]
    host: str | None
    owner: str
    repo: str
    ref: str | None
    rev: str | None


def is_commit_rev(s: str) -> bool:
    return len(s) == 40 and all(c in "0123456789abcdef" for c in s)


def parse_flake_reference(flake_url: str):
    if flake_url.startswith("flake:") or ":" not in flake_url:
        # indirect flake reference
        if flake_url.startswith("flake:"):
            flake_url = flake_url[len("flake:") :]
        parts = flake_url.split("/")
        flake_id = parts[0]
        ref = None
        rev = None
        if len(parts) == 2:
            if is_commit_rev(parts[1]):
                rev = parts[1]
            else:
                ref = parts[1]
        if len(parts) == 3:
            ref = parts[1]
            rev = parts[2]
        return IndirectFlakeReference(
            type="indirect", flake_id=flake_id, ref=ref, rev=rev
        )

    if flake_url.startswith("git:") or flake_url.startswith("git+"):
        if flake_url.startswith("git+ssh://"):
            protocol = "ssh"
            url = flake_url[len("git+ssh://") :]
        elif flake_url.startswith("git+http://"):
            protocol = "http"
            url = flake_url[len("git+http://") :]
        elif flake_url.startswith("git+https://"):
            protocol = "https"
            url = flake_url[len("git+https://") :]
        elif flake_url.startswith("git+file://"):
            protocol = "file"
            url = flake_url[len("git+file://") :]
        elif flake_url.startswith("git://"):
            protocol = "git"
            url = flake_url[len("git://") :]
        else:
            protocol = "git"
            url = flake_url[len("git:") :]

        url_parts = url.split("/")
        params = []
        host = None
        owner = None
        repo = None
        ref = None
        rev = None
        if len(url_parts) == 1:
            params = url_parts[0].split("?")
            repo = params[0].rstrip(".git")
        elif len(url_parts) == 2:
            owner = url_parts[0]
            params = url_parts[1].split("?")
            repo = params[0].rstrip(".git")
        elif len(url_parts) == 3:
            host = url_parts[0]
            owner = url_parts[1]
            params = url_parts[2].split("?")
            repo = params[0].rstrip(".git")

        for param in params[1:]:
            if param.startswith("ref="):
                ref = param[len("ref=") :]
            if param.startswith("rev="):
                rev = param[len("rev=") :]

        return GitFlakeReference(
            type="git",
            protocol=protocol,
            url=url,
            host=host,
            owner=owner,
            repo=repo,
            ref=ref,
            rev=rev,
        )

    if flake_url.startswith("github:"):
        url = flake_url[len("github:") :]
        parts = url.split("/")
        params = []
        host = None
        owner = None
        repo = None
        ref = None
        rev = None
        if len(parts) == 2:
            owner = parts[0]
            params = parts[1].split("?")
            repo = params[0]
        elif len(parts) == 3:
            owner = parts[0]
            repo = parts[1]
            params = parts[2].split("?")
            if is_commit_rev(parts[2]):
                rev = params[0]
            else:
                ref = params[0]

        for param in params[1:]:
            if param.startswith("ref="):
                ref = param[len("ref=") :]
            if param.startswith("rev="):
                rev = param[len("rev=") :]
            if param.startswith("host="):
                host = param[len("host=") :]

        return GithubFlakeReference(
            type="github",
            host=host,
            owner=owner,
            repo=repo,
            ref=ref,
            rev=rev,
        )


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
