"""The nix helpers and derivations that a project needs to build its settings.

They are copied into the `modules` directory of a project instead of being
imported from the thymis flake, so that a project keeps building with any
version of the flake (the controller and the device module of a project are
released separately, and existing projects pin the flake they were created
with).
"""

import logging
import pathlib
import shutil
from typing import Iterable

logger = logging.getLogger(__name__)

TEMPLATES = pathlib.Path(__file__).parent.parent / "templates_nix"

HELPERS_FILE = "module-settings.nix"


def write_project_module_files(modules_dir: pathlib.Path, modules: Iterable):
    """Copy the settings helpers and the derivations of `modules` into the
    `modules` directory of a project."""
    modules_dir.mkdir(parents=True, exist_ok=True)
    (modules_dir / "settings").mkdir(exist_ok=True)
    shutil.copyfile(TEMPLATES / HELPERS_FILE, modules_dir / HELPERS_FILE)
    for module in modules:
        if module.nix_derivation is not None:
            shutil.copyfile(
                TEMPLATES / "settings" / f"{module.nix_derivation}.nix",
                modules_dir / "settings" / f"{module.nix_derivation}.nix",
            )
        if module.nix_derivation_source is not None:
            (modules_dir / "settings" / f"{module.settings_namespace}.nix").write_text(
                module.nix_derivation_source
            )


def module_settings_files() -> list[pathlib.Path]:
    """The files that are copied into a project (for the module documentation
    and for tests)."""
    return [TEMPLATES / HELPERS_FILE] + sorted((TEMPLATES / "settings").glob("*.nix"))
