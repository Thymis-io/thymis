from typing import Literal

from pydantic import BaseModel


class ExternalRepoStatus(BaseModel):
    status: Literal[
        "loading", "no-url", "no-path", "no-readme", "no-magic-string", "loaded"
    ]
    modules: list[str] = []
    details: str | None = None


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
