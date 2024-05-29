from typing import Dict, List, Optional
from pydantic import BaseModel
import sys
import os
import pkgutil
import importlib
from .module import Module
import thymis_controller.models.modules


from thymis_controller.nix import get_input_out_path


class Repo(BaseModel):
    url: Optional[str] = None
    follows: Optional[str] = None
    inputs_follows: Dict[str, str] = {}


startup_python_path = sys.path.copy()
lockfile = None


def load_repositories(flake_path: os.PathLike, repositories: Dict[str, Repo]):
    # only run if lockfile changed
    global lockfile
    # lockfile sits at path/flake.lock
    lockfile_path = os.path.join(flake_path, "flake.lock")
    with open(lockfile_path, "r") as f:
        new_lockfile = f.read()
    if new_lockfile == lockfile:
        return
    lockfile = new_lockfile
    # for each repository: get_input_out_path from the flake.nix in the path
    input_out_paths = {}
    for name, repo in repositories.items():
        if not repo.url:
            continue
        path = get_input_out_path(flake_path, name)
        if path is None:
            continue
        # check wether path / README.md exists and contains the string "contains thymis modules"
        if not os.path.exists(os.path.join(path, "README.md")):
            print(f"Repository {name} does not contain a README.md")
            print(f"Skipping {name}")
            continue
        with open(os.path.join(path, "README.md"), "r") as f:
            if "contains thymis modules" not in f.read():
                print(f"Repository {name} contains no thymis modules")
                print(f"Skipping {name}")
                continue
        input_out_paths[name] = path
    # add the paths to sys.path
    sys.path = startup_python_path.copy()
    # for path in input_out_paths.values():
    modules_found = []
    for name, path in input_out_paths.items():
        print(f"Adding {name} at {path} to sys.path")
        sys.path.append(path)
        # print modules in path
        # print(list(pkgutil.iter_modules([path])))
        for module in pkgutil.walk_packages([path]):
            imported_module = importlib.import_module(module.name)
            for cls in imported_module.__dict__.values():
                if not isinstance(cls, type):
                    continue
                if issubclass(cls, Module) and cls != Module:
                    module_obj = cls()
                    modules_found.append(module_obj)
                    print(f"Found module {module_obj.type}")
    thymis_controller.models.modules.ALL_MODULES = (
        thymis_controller.models.modules.ALL_MODULES_START
    )
    thymis_controller.models.modules.ALL_MODULES.extend(modules_found)
