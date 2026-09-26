"""A module from an external repository, and how it meshes with the settings.

External repositories provide Thymis modules as python code; the settings of
such a module are written like the settings of a built-in module
(`settings_namespace` + `nix_attr_name`), and the module derives its NixOS
configuration from the merged settings with the helpers of
`nix/module-settings.nix`, which it imports from the thymis input of the project
or from a nix module it ships in its own repository.

This test stands in for that setup: the module below is defined outside the
thymis package and writes its derivation the way an external module would.
"""

import pathlib

import pytest
from tests.utils import nix_fixture
from thymis_controller import models
from thymis_controller.lib import HOST_PRIORITY
from thymis_controller.modules import modules

WHATEVER = "thymis_controller.modules.whatever.WhateverModule"

TAG_PRIORITY = 90


class ExternalStyleModule(modules.Module):
    display_name = "External Style Module"

    settings_namespace = "external-style"

    message = modules.Setting(
        display_name="Message",
        nix_attr_name="thymis.config.external-style.message",
        type="string",
        default="",
    )

    def write_nix_settings(self, f, path, module_settings, priority, project):
        # the settings of the instance, with their priorities
        super().write_nix_settings(f, path, module_settings, priority, project)

        # the derivation of the module: an external module imports the helpers
        # from the thymis input of the project (a module that ships a nix module
        # in its own repository imports them there instead)
        f.write(
            """
  systemd.services.external-style-message.description =
    (import (inputs.thymis + "/nix/module-settings.nix") { inherit config lib; })
      .apply "external-style" "message" "fallback";
"""
        )


def _module(settings):
    # the type of the module as the controller computes it from the class
    return models.ModuleSettings(type=ExternalStyleModule().type, settings=settings)


def _render(tmp_path: pathlib.Path, tag_settings, config_settings, custom_nix=None):
    tag = models.Tag(
        displayName="Base",
        identifier="base",
        priority=TAG_PRIORITY,
        modules=[_module(tag_settings)],
    )
    modules_ = [_module(config_settings)]
    if custom_nix is not None:
        modules_.append(
            models.ModuleSettings(type=WHATEVER, settings={"settings": custom_nix})
        )
    config = models.Config(
        displayName="c1", identifier="c1", tags=["base"], modules=modules_
    )
    return nix_fixture.render_project(
        tmp_path,
        tags=[tag],
        configs=[config],
        extra_modules=[ExternalStyleModule()],
    )


def _eval(tmp_path: pathlib.Path, expression: str, **kwargs):
    try:
        return nix_fixture.eval_project(_render(tmp_path, **kwargs), expression)
    except nix_fixture.NixUnavailable as e:
        pytest.skip(str(e))


EXPRESSION = """
let cfg = flake.nixosConfigurations.c1.config; in {
  message = cfg.systemd.services.external-style-message.description;
}
"""


def test_external_module_sees_the_settings_of_a_tag(tmp_path):
    """The derivation of an external module reads the merged settings, so a
    setting a tag provides is visible to a configuration that does not set it."""
    result = _eval(
        tmp_path,
        EXPRESSION,
        tag_settings={"message": "from-tag"},
        config_settings={},
    )
    assert result["message"] == "from-tag"


def test_external_module_derivation_wins_over_custom_nix(tmp_path):
    """The derived definition carries the priority of the setting, so it wins
    over custom nix of the same configuration (which has a higher priority
    number), and the configuration's value wins over the tag's."""
    result = _eval(
        tmp_path,
        EXPRESSION,
        tag_settings={"message": "from-tag"},
        config_settings={"message": "from-config"},
        custom_nix='systemd.services.external-style-message.description = "from-custom-nix";',
    )
    assert result["message"] == "from-config"


def test_external_module_writes_the_settings_of_its_instance(tmp_path):
    """The settings of the external module are written like the settings of a
    built-in module: one definition per setting, plus its priority."""
    project = _render(
        tmp_path, tag_settings={"message": "from-tag"}, config_settings={}
    )
    filename = f"{ExternalStyleModule().type}.nix"
    tag_file = (project / "tags" / "base" / filename).read_text()
    config_file = (project / "hosts" / "c1" / filename).read_text()
    assert (
        'thymis.config.external-style.message = lib.mkOverride 90 "from-tag";'
        in tag_file
    )
    assert "thymis.priority.external-style.message = lib.mkOverride 90 90;" in tag_file
    # the configuration does not set the message (and the module default is
    # empty), so it does not define a value that could shadow the tag's
    assert "thymis.config.external-style.message" not in config_file
    assert (
        "thymis.priority.external-style.message = lib.mkOverride 80 80;" in config_file
    )
    assert HOST_PRIORITY == 80
