from thymis_controller.models.external_repo import (
    GitFlakeReference,
    GithubFlakeReference,
    GitlabFlakeReference,
    IndirectFlakeReference,
)
from thymis_controller.nix.flake_reference import parse_flake_reference


def test_indirect_flake_reference():
    ref = parse_flake_reference("flake:nixpkgs")
    assert isinstance(ref, IndirectFlakeReference)
    assert ref.type == "indirect"
    assert ref.flake_id == "nixpkgs"
    assert ref.rev is None
    assert ref.ref is None

    ref = parse_flake_reference("nixpkgs")
    assert isinstance(ref, IndirectFlakeReference)
    assert ref.type == "indirect"
    assert ref.flake_id == "nixpkgs"
    assert ref.rev is None
    assert ref.ref is None

    ref = parse_flake_reference("nixpkgs/nixos-unstable")
    assert isinstance(ref, IndirectFlakeReference)
    assert ref.type == "indirect"
    assert ref.flake_id == "nixpkgs"
    assert ref.rev is None
    assert ref.ref == "nixos-unstable"

    ref = parse_flake_reference("nixpkgs/a3a3dda3bacf61e8a39258a0ed9c924eeca8e293")
    assert isinstance(ref, IndirectFlakeReference)
    assert ref.type == "indirect"
    assert ref.flake_id == "nixpkgs"
    assert ref.rev == "a3a3dda3bacf61e8a39258a0ed9c924eeca8e293"
    assert ref.ref is None

    ref = parse_flake_reference(
        "nixpkgs/nixos-unstable/a3a3dda3bacf61e8a39258a0ed9c924eeca8e293"
    )
    assert isinstance(ref, IndirectFlakeReference)
    assert ref.type == "indirect"
    assert ref.flake_id == "nixpkgs"
    assert ref.rev == "a3a3dda3bacf61e8a39258a0ed9c924eeca8e293"
    assert ref.ref == "nixos-unstable"


def test_git_flake_reference():
    ref = parse_flake_reference("git+ssh://git@github.com/NixOS/nix")
    assert isinstance(ref, GitFlakeReference)
    assert ref.type == "git"
    assert ref.protocol == "ssh"
    assert ref.url == "git@github.com/NixOS/nix"
    assert ref.host == "git@github.com"
    assert ref.owner == "NixOS"
    assert ref.repo == "nix"
    assert ref.ref is None
    assert ref.rev is None

    ref = parse_flake_reference("git+https://github.com/Thymis-io/thymis?ref=master")
    assert isinstance(ref, GitFlakeReference)
    assert ref.type == "git"
    assert ref.protocol == "https"
    assert ref.url == "github.com/Thymis-io/thymis?ref=master"
    assert ref.host == "github.com"
    assert ref.owner == "Thymis-io"
    assert ref.repo == "thymis"
    assert ref.ref == "master"
    assert ref.rev is None

    ref = parse_flake_reference(
        "git+https://github.com/Thymis-io/thymis.git?ref=master"
    )
    assert isinstance(ref, GitFlakeReference)
    assert ref.type == "git"
    assert ref.protocol == "https"
    assert ref.url == "github.com/Thymis-io/thymis.git?ref=master"
    assert ref.host == "github.com"
    assert ref.owner == "Thymis-io"
    assert ref.repo == "thymis"
    assert ref.ref == "master"
    assert ref.rev is None

    ref = parse_flake_reference(
        "git+https://github.com/Thymis-io/thymis.git?ref=feat/new-feature"
    )
    assert isinstance(ref, GitFlakeReference)
    assert ref.type == "git"
    assert ref.protocol == "https"
    assert ref.url == "github.com/Thymis-io/thymis.git?ref=feat/new-feature"
    assert ref.host == "github.com"
    assert ref.owner == "Thymis-io"
    assert ref.repo == "thymis"
    assert ref.ref == "feat/new-feature"
    assert ref.rev is None

    ref = parse_flake_reference("git+https://github.com/Thymis-io/thymis.git")
    assert isinstance(ref, GitFlakeReference)
    assert ref.type == "git"
    assert ref.protocol == "https"
    assert ref.url == "github.com/Thymis-io/thymis.git"
    assert ref.host == "github.com"
    assert ref.owner == "Thymis-io"
    assert ref.repo == "thymis"
    assert ref.ref is None
    assert ref.rev is None

    ref = parse_flake_reference("git+file:///home/projects/thymis/thymis")
    assert isinstance(ref, GitFlakeReference)
    assert ref.type == "git"
    assert ref.protocol == "file"
    assert ref.url == "/home/projects/thymis/thymis"
    assert ref.host is None
    assert ref.owner is None
    assert ref.repo is None
    assert ref.ref is None
    assert ref.rev is None


def test_github_flake_reference():
    ref = parse_flake_reference("github:NixOS/nix")
    assert isinstance(ref, GithubFlakeReference)
    assert ref.type == "github"
    assert ref.host is None
    assert ref.owner == "NixOS"
    assert ref.repo == "nix"
    assert ref.ref is None
    assert ref.rev is None

    ref = parse_flake_reference("github:NixOS/nix/master")
    assert isinstance(ref, GithubFlakeReference)
    assert ref.type == "github"
    assert ref.host is None
    assert ref.owner == "NixOS"
    assert ref.repo == "nix"
    assert ref.ref == "master"
    assert ref.rev is None

    ref = parse_flake_reference("github:NixOS/nix/feature/awesome")
    assert isinstance(ref, GithubFlakeReference)
    assert ref.type == "github"
    assert ref.host is None
    assert ref.owner == "NixOS"
    assert ref.repo == "nix"
    assert ref.ref == "feature/awesome"
    assert ref.rev is None

    # veloren/dev is a subgroup and is URL-encoded
    ref = parse_flake_reference("gitlab:veloren%2Fdev/rfcs")
    assert isinstance(ref, GitlabFlakeReference)
    assert ref.type == "gitlab"
    assert ref.host is None
    assert ref.owner == "veloren/dev"
    assert ref.repo == "rfcs"
    assert ref.ref is None
    assert ref.rev is None

    ref = parse_flake_reference(
        "github:NixOS/nix/a3a3dda3bacf61e8a39258a0ed9c924eeca8e293"
    )
    assert isinstance(ref, GithubFlakeReference)
    assert ref.type == "github"
    assert ref.host is None
    assert ref.owner == "NixOS"
    assert ref.repo == "nix"
    assert ref.ref is None
    assert ref.rev == "a3a3dda3bacf61e8a39258a0ed9c924eeca8e293"

    ref = parse_flake_reference(
        "github:internal/project?host=company-github.example.org"
    )
    assert isinstance(ref, GithubFlakeReference)
    assert ref.type == "github"
    assert ref.host == "company-github.example.org"
    assert ref.owner == "internal"
    assert ref.repo == "project"
    assert ref.ref is None
    assert ref.rev is None


def test_gitlab_flake_reference():
    ref = parse_flake_reference("gitlab:veloren/veloren")
    assert isinstance(ref, GitlabFlakeReference)
    assert ref.type == "gitlab"
    assert ref.host is None
    assert ref.owner == "veloren"
    assert ref.repo == "veloren"
    assert ref.ref is None
    assert ref.rev is None

    ref = parse_flake_reference("gitlab:veloren/veloren/master")
    assert isinstance(ref, GitlabFlakeReference)
    assert ref.type == "gitlab"
    assert ref.host is None
    assert ref.owner == "veloren"
    assert ref.repo == "veloren"
    assert ref.ref == "master"
    assert ref.rev is None

    ref = parse_flake_reference("gitlab:veloren/veloren/feature/awesome")
    assert isinstance(ref, GitlabFlakeReference)
    assert ref.type == "gitlab"
    assert ref.host is None
    assert ref.owner == "veloren"
    assert ref.repo == "veloren"
    assert ref.ref == "feature/awesome"
    assert ref.rev is None

    ref = parse_flake_reference(
        "gitlab:veloren/veloren/80a4d7f13492d916e47d6195be23acae8001985a"
    )
    assert isinstance(ref, GitlabFlakeReference)
    assert ref.type == "gitlab"
    assert ref.host is None
    assert ref.owner == "veloren"
    assert ref.repo == "veloren"
    assert ref.ref is None
    assert ref.rev == "80a4d7f13492d916e47d6195be23acae8001985a"

    ref = parse_flake_reference("gitlab:openldap/openldap?host=git.openldap.org")
    assert isinstance(ref, GitlabFlakeReference)
    assert ref.type == "gitlab"
    assert ref.host == "git.openldap.org"
    assert ref.owner == "openldap"
    assert ref.repo == "openldap"
    assert ref.ref is None
    assert ref.rev is None
