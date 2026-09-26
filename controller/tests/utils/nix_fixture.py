"""Helpers to render a thymis project repository and evaluate the nix that the
controller generates from it.

The generated repository is a flake of its own which takes this repository as
its `thymis` input, so evaluating it exercises the whole pipeline: module
settings, the generated module files, the nix module system merging them, and
the settings translation in `nix/settings/`.
"""

import json
import pathlib
import shutil
import subprocess

from thymis_controller import models
from thymis_controller.lib import HOST_PRIORITY
from thymis_controller.modules.builtin_modules import ALL_MODULES
from thymis_controller.nix.module_settings import write_project_module_files
from thymis_controller.nix.templating import render_flake_nix

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

_MODULES = {module.type: module for module in ALL_MODULES}


class NixUnavailable(RuntimeError):
    pass


DEVICE = "thymis_controller.modules.thymis.ThymisDevice"


class _Project:
    """The modules that name their systemd units after their source path need the
    project the module files are written into."""

    def __init__(self, path: pathlib.Path):
        self.path = path


def _write_modules(
    root: pathlib.Path, kind: str, identifier: str, modules, priority: int
):
    path = root / kind / identifier
    path.mkdir(parents=True, exist_ok=True)
    project = _Project(root)
    for module_settings in modules:
        module = _MODULES[module_settings.type]
        # the real writer, so that the generated files are exactly what the
        # controller produces
        module.write_nix(path, module_settings, priority, project)


def _device_module(identifier: str) -> models.ModuleSettings:
    """Every real device configuration has a ThymisDevice module; it selects the
    device type module, which is what sets the host platform of the evaluation."""
    return models.ModuleSettings(
        type=DEVICE,
        settings={
            "device_type": "generic-x86_64",
            "image_format": "nixos-vm",
            "device_name": identifier,
        },
    )


def render_project(
    tmp_path: pathlib.Path, tags=None, configs=None, extra_modules=None
) -> pathlib.Path:
    """Render a project repository for `tags` and `configs` into `tmp_path`.

    `extra_modules` registers additional module instances (e.g. a module that
    stands in for a module from an external repository).
    """
    for module in extra_modules or []:
        _MODULES[module.type] = module
    root = tmp_path / "project"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    repositories = {
        "thymis": models.Repo(url=f"path:{REPO_ROOT}"),
        "nixpkgs": models.Repo(follows="thymis/nixpkgs"),
    }
    (root / "flake.nix").write_text(render_flake_nix(repositories))
    state = models.State(tags=list(tags or []), configs=list(configs or []))
    for config in state.configs:
        if not any(module.type == DEVICE for module in config.modules):
            config.modules.insert(0, _device_module(config.identifier))
    (root / "state.json").write_text(state.model_dump_json(indent=2))
    # the settings helpers and the derivations of the modules the project uses
    write_project_module_files(
        root / "modules",
        list(
            dict.fromkeys(
                _MODULES[module_settings.type]
                for module_settings in [
                    module for config in state.configs for module in config.modules
                ]
                + [module for tag in state.tags for module in tag.modules]
                if module_settings.type in _MODULES
            )
        ),
    )
    for config in state.configs:
        _write_modules(root, "hosts", config.identifier, config.modules, HOST_PRIORITY)
    for tag in state.tags:
        _write_modules(root, "tags", tag.identifier, tag.modules, tag.priority)
    return root


def eval_project(root: pathlib.Path, expression: str):
    """Evaluate `expression` in the scope of the flake generated at `root`.

    The expression can use `flake`, the evaluated generated repository, e.g.
    `flake.nixosConfigurations.c1.config.networking.interfaces`.
    """
    if shutil.which("nix") is None:
        raise NixUnavailable("nix is not available")
    result = subprocess.run(
        [
            "nix",
            "eval",
            "--impure",
            "--json",
            "--expr",
            f'let flake = builtins.getFlake "{root}"; in {expression}',
        ],
        capture_output=True,
        text=True,
        cwd=root,
    )
    if result.returncode != 0:
        raise AssertionError(f"nix eval failed:\n{result.stderr[-8000:]}")
    return json.loads(result.stdout)
