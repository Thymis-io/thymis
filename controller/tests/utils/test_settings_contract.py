"""The contract every module follows when its settings are written to nix.

Each setting is written as `lib.mkOverride <priority>` definitions:
- the priority is always a number (a quoted priority makes nix fail with
  "cannot compare a string with an integer"),
- a setting that declares a `nix_attr_name` is always written somewhere under
  that path when it is configured (no setting is silently dropped, which is what
  happens when a module renders a setting through python code without a
  definition of its own),
- modules with a `settings_namespace` publish the priority of every setting so
  that the nix side can derive NixOS configuration from the merged settings.
"""

import io
import pathlib

import pytest
from thymis_controller import models
from thymis_controller.modules import modules as modules_lib
from thymis_controller.modules.builtin_modules import ALL_MODULES
from thymis_controller.modules.modules import ListType, SelectOneType

PRIORITY = 80


class _Project:
    """The modules that name their systemd units after their source path need
    the project the module file is written into."""

    path = pathlib.Path("/tmp/project")


def _value_for(setting: modules_lib.Setting):
    setting_type = setting.type
    if isinstance(setting_type, SelectOneType):
        return setting_type.select_one[0][1]
    if isinstance(setting_type, ListType):
        element = {
            key: _value_for(sub_setting)
            for key, sub_setting in setting_type.settings.items()
        }
        return [element]
    if isinstance(setting_type, modules_lib.SecretType):
        return "secret-value"
    if isinstance(setting_type, modules_lib.ArtifactType):
        return "artifact.bin"
    if isinstance(setting_type, modules_lib.TextAreaCodeType):
        return "config"
    if isinstance(setting_type, modules_lib.SystemdTimerType):
        return {"timer_type": "realtime", "on_calendar": ["daily"]}
    if setting_type == "bool":
        return True
    if setting_type == "int":
        return 12
    return "value"


def _render(module: modules_lib.Module) -> str:
    settings = {}
    for attr, setting in module.iter_settings().items():
        value = _value_for(setting)
        if value is None:
            continue
        settings[attr] = value
    f = io.StringIO()
    module.write_nix_settings(
        f,
        pathlib.Path("/tmp/project/repository/hosts/c1"),
        models.ModuleSettings(type=module.type, settings=settings),
        PRIORITY,
        _Project(),
    )
    return f.getvalue()


@pytest.mark.parametrize("module", ALL_MODULES, ids=lambda m: m.type.rsplit(".", 1)[-1])
def test_all_settings_are_written_as_numbered_definitions(module):
    out = _render(module)

    # quoted priorities make nix fail to merge the definition
    assert 'lib.mkOverride "' not in out

    for attr, setting in module.iter_settings().items():
        if setting.nix_attr_name is not None:
            prefix = f"{setting.nix_attr_name}."
            assert (
                f"  {setting.nix_attr_name} = lib.mkOverride" in out or prefix in out
            ), f"{module.type}.{attr} is not written to {setting.nix_attr_name}"
        if module.settings_namespace is not None:
            namespace = f"thymis.priority.{module.settings_namespace}.{attr}"
            assert (
                f"  {namespace} = lib.mkOverride {PRIORITY} {PRIORITY};" in out
            ), f"{module.type}.{attr} does not publish its priority"
