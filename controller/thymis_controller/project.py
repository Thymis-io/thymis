import importlib
import json
import logging
import os
import pathlib
import pkgutil
import shutil
import subprocess
import sys
import tempfile
import threading
import traceback
from pathlib import Path
from typing import List

import git
from sqlalchemy.orm import Session
from thymis_controller import crud, migration, models, task
from thymis_controller.config import global_settings
from thymis_controller.models import history
from thymis_controller.models.state import State
from thymis_controller.nix import NIX_CMD, get_input_out_path, render_flake_nix
from thymis_controller.notifications import notification_manager

logger = logging.getLogger(__name__)

BUILTIN_REPOSITORIES = {
    "thymis": models.Repo(url="github:thymis-io/thymis"),
    "nixpkgs": models.Repo(follows="thymis/nixpkgs"),
}

HOST_PRIORITY = 80


def del_path(path: os.PathLike):
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


startup_python_path = sys.path.copy()

lockfile = None


def load_repositories(flake_path: os.PathLike, repositories: dict[str, models.Repo]):
    from thymis_controller import modules

    # only run if lockfile changed
    global lockfile
    # lockfile sits at path/flake.lock
    lockfile_path = os.path.join(flake_path, "flake.lock")
    with open(lockfile_path, "r", encoding="utf-8") as f:
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
            logger.warning("Repository %s does not contain a README.md", name)
            logger.warning("Skipping %s", name)
            continue
        with open(os.path.join(path, "README.md"), "r", encoding="utf-8") as f:
            if "contains thymis modules" not in f.read():
                logger.warning("Repository %s contains no thymis modules", name)
                logger.warning("Skipping %s", name)
                continue
        input_out_paths[name] = path
    # add the paths to sys.path
    sys.path = startup_python_path.copy()
    # for path in input_out_paths.values():
    importlib.invalidate_caches()
    modules_found = []
    for name, path in input_out_paths.items():
        logger.info("Adding %s at %s to sys.path", name, path)
        sys.path.append(path)
        for module in pkgutil.walk_packages([path]):
            try:
                imported_module = importlib.import_module(module.name)
                # required to detect changes if this is a second import
                importlib.reload(imported_module)
                logger.info("Imported module %s", module.name)
                for name, value in imported_module.__dict__.items():
                    logger.info("Checking value %s", name)
                    if not isinstance(value, type):
                        continue
                    cls = value
                    logger.info("Found class %s", cls)
                    if issubclass(cls, modules.Module) and cls != modules.Module:
                        module_obj = cls()
                        modules_found.append(module_obj)
                        logger.info("Found module %s", module_obj.type)
            except Exception as e:  # pylint: disable=broad-except
                traceback.print_exc()
                logger.error("Error while importing module %s: %s", module.name, e)
    modules.ALL_MODULES = modules.ALL_MODULES_START.copy()
    modules.ALL_MODULES.extend(modules_found)


def get_module_class_instance_by_type(module_type: str):
    # split the module_type by .
    module_type = module_type.rsplit(".", 1)
    # import the module
    try:
        module = importlib.import_module(module_type[0])
        # get the class from the module
        cls = getattr(module, module_type[1])
        # return an instance of the class
        return cls()
    except Exception as e:
        raise Exception(
            f"Error while importing module {module_type}: {e}"
        ) from e  # pylint: disable=broad-exception-raised


class Project:
    path: pathlib.Path
    repo: git.Repo
    known_hosts_path: pathlib.Path
    public_key: str
    history_lock = threading.Lock()

    def __init__(self, path, db_session: Session):
        self.path = pathlib.Path(path)
        # create the path if not exists
        self.path.mkdir(exist_ok=True, parents=True)
        # create a git repo if not exists
        if not (self.path / ".git").exists():
            print("Initializing git repo")
            self.repo = git.Repo.init(self.path)
        else:
            self.repo = git.Repo(self.path)

        # get public key of controller instance
        public_key_process = subprocess.run(
            ["ssh-keygen", "-y", "-f", global_settings.SSH_KEY_PATH, "-P", ""],
            capture_output=True,
            text=True,
        )

        if public_key_process.returncode != 0:
            logger.error("Failed to get public key: %s", public_key_process.stderr)
            self.public_key = None
        else:
            self.public_key = public_key_process.stdout.strip()

        # create a state, if not exists
        state_path = self.path / "state.json"
        if not state_path.exists():
            self.write_state_and_reload(State())
        # migrate the state and write it back now
        with open(state_path, "r", encoding="utf-8") as f:
            state_dict = json.load(f)
        state_dict = migration.migrate(state_dict)
        try:
            self.write_state_and_reload(State.model_validate(state_dict))
        except subprocess.CalledProcessError as e:
            logger.error("Error while migrating state: %s", e)
            traceback.print_exc()

        logger.info("Initializing known_hosts file")
        self.known_hosts_path = None
        self.update_known_hosts(db_session)

    def read_state(self):
        with open(Path(self.path) / "state.json", "r", encoding="utf-8") as f:
            state_json = f.read()
        state = State.model_validate_json(state_json)
        return state

    def write_state_and_reload(self, state: State):
        with open(self.path / "state.json", "w", encoding="utf-8") as f:
            f.write(state.model_dump_json(indent=2))
        # write a flake.nix
        repositories = BUILTIN_REPOSITORIES | state.repositories
        with open(self.path / "flake.nix", "w+", encoding="utf-8") as f:
            f.write(render_flake_nix(repositories))
        self.repo.git.add(".")
        # write missing flake.lock entries using nix flake lock
        subprocess.run(
            ["nix", *NIX_CMD[1:], "flake", "lock"], cwd=self.path, check=True
        )
        self.set_repositories_in_python_path(self.path, state)
        # create modules folder if not exists
        modules_path = self.path / "modules"
        del_path(modules_path)
        modules_path.mkdir(exist_ok=True)
        # create and empty hosts, tags folder
        del_path(self.path / "hosts")
        del_path(self.path / "tags")
        (self.path / "hosts").mkdir(exist_ok=True)
        (self.path / "tags").mkdir(exist_ok=True)
        # for each host create its own folder
        for device in state.devices:
            # assert device.identifier, "identifier cannot be empty"
            if not device.identifier:
                logger.info("Device with empty identifier found, skipping")
                continue
            self.create_folder_and_write_modules(
                "hosts", device.identifier, device.modules, HOST_PRIORITY
            )
        for tag in state.tags:
            self.create_folder_and_write_modules(
                "tags", tag.identifier, tag.modules, tag.priority
            )
        self.repo.git.add(".")

    def create_folder_and_write_modules(self, base_path, identifier, modules, priority):
        path = self.path / base_path / identifier
        path.mkdir(exist_ok=True)
        os.mknod(path / ".gitkeep")
        for module_settings in modules:
            try:
                module = get_module_class_instance_by_type(module_settings.type)
                module.write_nix(path, module_settings, priority, self)
            except Exception as e:
                logger.error(
                    "Error while writing module %s: %s", module_settings.type, e
                )
                traceback.print_exc()

    def set_repositories_in_python_path(self, path: os.PathLike, state: State):
        repositories = BUILTIN_REPOSITORIES | state.repositories
        load_repositories(path, repositories)

    def commit(self, summary: str):
        self.repo.git.add(".")
        try:
            if self.repo.index.diff("HEAD"):
                self.repo.index.commit(summary)
                logger.info("Committed changes: %s", summary)
        except git.BadName:
            self.repo.index.commit(summary)

        self.pull_git()

        try:
            self.repo.git.push()
        except git.GitCommandError as e:
            traceback.print_exc()
            message = (
                f"{' '.join(e.command)} failed with status code {e.status}{e.stderr}"
            )
            notification_manager.broadcast(message)

    def get_history(self):
        try:
            with self.history_lock:
                return [
                    history.Commit(
                        message=commit.message,
                        author=commit.author.name,
                        date=commit.authored_datetime,
                        SHA=commit.hexsha,
                        SHA1=self.repo.git.rev_parse(commit.hexsha, short=True),
                        state_diff=self.repo.git.diff(
                            commit.hexsha,
                            (
                                commit.parents[0].hexsha
                                if len(commit.parents) > 0
                                else None
                            ),
                            "-R",
                            "state.json",
                            unified=5,
                        ).split("\n")[4:],
                    )
                    for commit in self.repo.iter_commits()
                ]
        except Exception as e:
            traceback.print_exc()
            notification_manager.broadcast(str(e))
            return []

    def update_known_hosts(self, db_session: Session):
        if not self.known_hosts_path or not self.known_hosts_path.exists():
            self.known_hosts_path = pathlib.Path(
                tempfile.NamedTemporaryFile(delete=False).name
            )

        hostkeys = crud.hostkey.get_all(db_session)
        with open(self.known_hosts_path, "w", encoding="utf-8") as f:
            for hostkey in hostkeys:
                f.write(f"{hostkey.device_host} {hostkey.public_key}\n")

        logger.info("Updated known_hosts file at %s", self.known_hosts_path)

    def revert_commit(self, commit: str):
        commit_to_revert = self.repo.commit(commit)
        sha1 = self.repo.git.rev_parse(commit_to_revert.hexsha, short=True)
        self.repo.git.rm("-r", ".")
        self.repo.git.checkout(commit_to_revert.hexsha, ".")
        self.repo.index.commit(f"Revert to {sha1}: {commit_to_revert.message}")
        logger.info(f"Reverted commit: {commit_to_revert}")

    def clone_state_device(
        self, device_identifier, new_device_identifier, new_device_display_name=None
    ):
        state = self.read_state()
        device = next(
            device for device in state.devices if device.identifier == device_identifier
        )
        new_device = device.model_copy()
        new_device.identifier = new_device_identifier
        if new_device_display_name:
            new_device.displayName = new_device_display_name(device.displayName)
        state.devices.append(new_device)
        self.write_state_and_reload(state)

    def get_remotes(self):  #
        return [
            history.Remote(
                name=remote.name,
                url=remote.url,
                branches=[ref.name for ref in remote.refs],
            )
            for remote in self.repo.remotes
        ]

    def git_ahead_count(self, from_ref: str, to_ref: str):
        return self.repo.git.rev_list(f"{from_ref}..{to_ref}", count=True)

    def git_info(self):
        active_branch = self.repo.active_branch
        tracking_branch = active_branch.tracking_branch()

        if tracking_branch:
            ahead = self.git_ahead_count(tracking_branch.name, active_branch.name)
            behind = self.git_ahead_count(active_branch.name, tracking_branch.name)
        else:
            ahead = 0
            behind = 0

        return history.GitInfo(
            active_branch=self.repo.active_branch.name,
            remote_branch=tracking_branch.name if tracking_branch else None,
            ahead=ahead,
            behind=behind,
            remotes=self.get_remotes(),
        )

    def has_git_remote(self, name: str):
        return name in [remote.name for remote in self.repo.remotes]

    def add_git_remote(self, remote: history.Remote):
        self.repo.create_remote(remote.name, remote.url)

    def update_git_remote(
        self,
        name: str,
        remote_update: history.Remote,
    ):
        if name != remote_update.name:
            self.repo.git.remote("rename", name, remote_update.name)
        if self.repo.remote(remote_update.name).url != remote_update.url:
            self.repo.git.remote("set-url", remote_update.name, remote_update.url)
        self.pull_git()

    def delete_git_remote(self, name: str):
        self.repo.delete_remote(name)

    def switch_remote_branch(self, branch: str):
        try:
            self.repo.git.branch(
                self.repo.active_branch.name, f"--set-upstream-to={branch}"
            )
        except git.GitCommandError as e:
            traceback.print_exc()
            notification_manager.broadcast(str(e))
        self.pull_git()

    def fetch_git(self):
        self.repo.git.fetch("--all")

    def pull_git(self):
        try:
            # fail if git askings for credentials to avoid blocking
            os.environ["GIT_TERMINAL_PROMPT"] = "0"
            self.repo.git.pull("--ff-only")
        except git.GitCommandError as e:
            traceback.print_exc()
            stderr = e.stderr.replace("hint:", "\t").replace("\n\t\n", "\n")
            if "terminal prompts disabled" in stderr:
                remote = self.git_info().remote_branch
                message = f"Failed to pull from git remote {remote}: repository not found or credentials missing"
            else:
                message = (
                    f"{' '.join(e.command)} failed with status code {e.status}{stderr}"
                )
            notification_manager.broadcast(message)

    def create_build_task(self):
        return task.global_task_controller.add_task(task.BuildProjectTask(self.path))

    def create_deploy_device_task(self, device_identifier: str, target_host: str):
        device = next(
            device
            for device in self.read_state().devices
            if device.identifier == device_identifier
        )
        return task.global_task_controller.add_task(
            task.DeployDeviceTask(
                self.path, device, target_host, global_settings.SSH_KEY_PATH
            )
        )

    def create_deploy_project_task(self, devices: List[models.Hostkey]):
        return task.global_task_controller.add_task(
            task.DeployProjectTask(self, devices, global_settings.SSH_KEY_PATH)
        )

    def create_update_task(self):
        return task.global_task_controller.add_task(task.UpdateTask(self.path, self))

    def create_build_device_image_task(
        self,
        device_identifier: str,
        db_session: Session,
    ):
        self.commit(f"Build image for {device_identifier}")
        device_state = next(
            device
            for device in self.read_state().devices
            if device.identifier == device_identifier
        )
        return task.global_task_controller.add_task(
            task.BuildDeviceImageTask(
                self.path,
                device_identifier,
                db_session,
                device_state.model_dump(),
                self.repo.head.object.hexsha,
            )
        )

    def create_restart_device_task(self, device: models.Device, target_host: str):
        return task.global_task_controller.add_task(
            task.RestartDeviceTask(
                device, global_settings.SSH_KEY_PATH, self.known_hosts_path, target_host
            )
        )
