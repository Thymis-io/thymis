from thymis_controller.crud.external_repositories import (
    GitFlakeReference,
    GithubFlakeReference,
    IndirectFlakeReference,
    parse_flake_reference,
)


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
