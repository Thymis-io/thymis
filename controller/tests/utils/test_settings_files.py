"""Translation of the Files module settings into NixOS configuration.

The artifacts of the Files module are merged by the nix module system as an
attribute set keyed by the path they are placed at, and `nix/settings/files.nix`
derives `systemd.tmpfiles.rules` from the merged value. Artifacts of the device
configuration and of tags therefore end up in one rule list instead of
replacing each other, and the derived rules are contributed to the option
instead of overriding it, so the rules of the device module and of nixpkgs stay
in place.
"""

import pathlib

import pytest
from tests.utils import nix_fixture
from thymis_controller import models

FILES = "thymis_controller.modules.files.FilesModule"
DEVICE = "thymis_controller.modules.thymis.ThymisDevice"
WHATEVER = "thymis_controller.modules.whatever.WhateverModule"

TAG_PRIORITY = 90

# the raw custom nix both configurations write for `systemd.tmpfiles.rules`
CUSTOM_RULE = "C+ /custom 0755 root root - /custom"

# content of the artifact files the rendered project carries
ARTIFACTS = {"app.bin": "app", "thing.cfg": "thing"}

EXPRESSION = """
let
  c1 = flake.nixosConfigurations.c1;
  pkgs = c1.pkgs;
  files = c1.config.thymis.config.files;
in {
  rules = c1.config.systemd.tmpfiles.rules;
  # the very expression the old python rendering interpolated into the rule
  appStorePath = pkgs.copyPathToStore (flake.outPath + "/artifacts/app.bin");
  thingStorePath = pkgs.copyPathToStore (flake.outPath + "/artifacts/thing.cfg");
  secretPaths = builtins.attrNames files.secrets;
  tagSecretOwner = files.secrets."/run/tag".owner;
  configSecretMode = files.secrets."/run/cfg".mode;
}
"""

# the second scenario has no artifacts directory and no secrets
METADATA_ONLY_EXPRESSION = """
let
  c1 = flake.nixosConfigurations.c1;
in {
  rules = c1.config.systemd.tmpfiles.rules;
  metadataOnlyArtifactMode = c1.config.thymis.config.files.artifacts."/etc/no-artifact".mode;
}
"""


def _files(settings):
    return models.ModuleSettings(type=FILES, settings=settings)


def _custom_nix(settings):
    return models.ModuleSettings(type=WHATEVER, settings={"settings": settings})


def _device():
    # the device type provides nixpkgs.hostPlatform
    return models.ModuleSettings(
        type=DEVICE, settings={"device_type": "generic-x86_64"}
    )


def _render_artifacts_from_all_sources(tmp_path: pathlib.Path):
    """A tag artifact and a configuration artifact, plus raw custom rules."""
    tag = models.Tag(
        displayName="Base",
        identifier="base",
        priority=TAG_PRIORITY,
        modules=[
            _files(
                {
                    "artifacts": [{"artifact": "app.bin", "path": "/opt/app"}],
                    "secrets": [
                        {"secret": "tagsecret", "path": "/run/tag", "owner": "root"}
                    ],
                }
            )
        ],
    )
    config = models.Config(
        displayName="c1",
        identifier="c1",
        tags=["base"],
        modules=[
            _device(),
            _files(
                {
                    "artifacts": [
                        {
                            "artifact": "thing.cfg",
                            "path": "/etc/thing",
                            "mode": "0644",
                        }
                    ],
                    "secrets": [
                        {"secret": "cfgsecret", "path": "/run/cfg", "mode": "0400"}
                    ],
                }
            ),
            _custom_nix(f'systemd.tmpfiles.rules = [ "{CUSTOM_RULE}" ];'),
        ],
    )
    root = nix_fixture.render_project(tmp_path, tags=[tag], configs=[config])
    artifacts = root / "artifacts"
    artifacts.mkdir()
    for name, content in ARTIFACTS.items():
        (artifacts / name).write_text(content)
    return root


def _render_artifact_element_without_artifact(tmp_path: pathlib.Path):
    """An artifact element that only carries placement metadata."""
    config = models.Config(
        displayName="c1",
        identifier="c1",
        tags=[],
        modules=[
            _device(),
            _files({"artifacts": [{"path": "/etc/no-artifact", "mode": "0644"}]}),
            _custom_nix(f'systemd.tmpfiles.rules = [ "{CUSTOM_RULE}" ];'),
        ],
    )
    return nix_fixture.render_project(tmp_path, tags=[], configs=[config])


def _eval(tmp_path: pathlib.Path, render, expression: str):
    try:
        return nix_fixture.eval_project(render(tmp_path), expression)
    except nix_fixture.NixUnavailable as e:
        pytest.skip(str(e))


def test_artifacts_of_all_sources_merge_into_tmpfiles_rules(tmp_path):
    result = _eval(tmp_path, _render_artifacts_from_all_sources, EXPRESSION)

    # the rule format of the old python rendering: `C+ <path> <mode> <owner>
    # <group> - <artifact in the store>`, with the tmpfiles default for the
    # metadata the setting leaves unset
    app_rule = f"C+ /opt/app - - - - {result['appStorePath']}"
    thing_rule = f"C+ /etc/thing 0644 - - - {result['thingStorePath']}"

    # the configuration artifact and the tag artifact are both placed, neither
    # replaces the other
    assert thing_rule in result["rules"]
    assert app_rule in result["rules"]

    # the derived rules are contributed to the option, they do not replace the
    # rules other sources define for it
    assert any(rule.startswith("f /etc/hostname ") for rule in result["rules"])
    assert CUSTOM_RULE in result["rules"]


def test_secrets_keep_their_settings_mapping(tmp_path):
    result = _eval(tmp_path, _render_artifacts_from_all_sources, EXPRESSION)

    # secrets are placed by the agent at runtime, so they derive no tmpfiles
    # rule, but they are still written 1:1 and merged per path
    assert result["secretPaths"] == ["/run/cfg", "/run/tag"]
    assert result["tagSecretOwner"] == "root"
    assert result["configSecretMode"] == "0400"
    assert all("secret" not in rule for rule in result["rules"])


def test_artifact_element_without_artifact_defines_no_rules(tmp_path):
    result = _eval(
        tmp_path, _render_artifact_element_without_artifact, METADATA_ONLY_EXPRESSION
    )

    # the element is written to the settings ...
    assert result["metadataOnlyArtifactMode"] == "0644"
    # ... but derives no rule, and a Files module without artifacts must not
    # define one
    assert CUSTOM_RULE in result["rules"]
    assert all("/etc/no-artifact" not in rule for rule in result["rules"])
