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
    written: dict[pathlib.Path, str] = {}
    for module in modules:
        if module.nix_derivation is not None:
            source = TEMPLATES / "settings" / f"{module.nix_derivation}.nix"
            if not source.is_file():
                raise FileNotFoundError(
                    f"module {module.type} declares nix_derivation "
                    f"{module.nix_derivation!r}, but {source} does not exist"
                )
            target = modules_dir / "settings" / f"{module.nix_derivation}.nix"
            content = source.read_text()
            _write_checked(written, target, content)
        if module.nix_derivation_source is not None:
            if module.settings_namespace is None:
                raise ValueError(
                    f"module {module.type} ships nix_derivation_source but sets "
                    "no settings_namespace; the file name of the derivation is "
                    "the namespace"
                )
            target = modules_dir / "settings" / f"{module.settings_namespace}.nix"
            _write_checked(written, target, module.nix_derivation_source)


def _write_checked(
    written: dict[pathlib.Path, str], target: pathlib.Path, content: str
) -> None:
    """Write a copied derivation, refusing to let one module silently replace
    the file another module contributed."""
    previous = written.get(target)
    if previous is not None and previous != content:
        raise ValueError(
            f"two modules contribute different content for {target}; "
            "each module needs its own nix_derivation name or settings_namespace"
        )
    written[target] = content
    target.write_text(content)


def module_settings_files() -> list[pathlib.Path]:
    """The files that are copied into a project (for the module documentation
    and for tests)."""
    return [TEMPLATES / HELPERS_FILE] + sorted((TEMPLATES / "settings").glob("*.nix"))
