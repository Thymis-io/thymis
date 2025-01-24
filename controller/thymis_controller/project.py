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

import git
import paramiko
import sqlalchemy
import sqlalchemy.orm
from thymis_controller import crud, migration, models, task
from thymis_controller.config import global_settings
from thymis_controller.models import history
from thymis_controller.models.state import State
from thymis_controller.nix import NIX_CMD, get_input_out_path, render_flake_nix

logger = logging.getLogger(__name__)

if "THYMIS_FLAKE_ROOT" in os.environ:
    thymis_repo = models.Repo(
        url=f"git+file://{pathlib.Path(os.environ['THYMIS_FLAKE_ROOT']).resolve()}"
    )
else:
    thymis_repo = models.Repo(url="github:thymis-io/thymis/v0.3")


BUILTIN_REPOSITORIES = {
    "thymis": thymis_repo,
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
            logger.debug("Repository %s does not contain a README.md", name)
            logger.debug("Skipping %s", name)
            continue
        with open(os.path.join(path, "README.md"), "r", encoding="utf-8") as f:
            if "contains thymis modules" not in f.read():
                logger.debug("Repository %s contains no thymis modules", name)
                logger.debug("Skipping %s", name)
                continue
        logger.info("Found repository %s at %s", name, path)
        input_out_paths[name] = path
    # add the paths to sys.path
    sys.path = startup_python_path.copy()
    # for path in input_out_paths.values():
    importlib.invalidate_caches()
    modules_found = []
    for name, path in input_out_paths.items():
        logger.debug("Adding %s at %s to sys.path", name, path)
        sys.path.append(path)
        for module in pkgutil.walk_packages([path]):
            try:
                imported_module = importlib.import_module(module.name)
                # required to detect changes if this is a second import
                importlib.reload(imported_module)
                logger.debug("Imported module %s", module.name)
                for name, value in imported_module.__dict__.items():
                    # logger.info("Checking value %s", name)
                    if not isinstance(value, type):
                        continue
                    cls = value
                    logger.debug("Found class %s", cls)
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
    repo_dir: pathlib.Path

    def __init__(self, path, db_session: sqlalchemy.orm.Session):
        self.path = pathlib.Path(path)
        # create the path if not exists
        self.path.mkdir(exist_ok=True, parents=True)
        self.repo_dir = self.path / "repository"
        # create a git repo if not exists
        if not (self.path / ".git").exists():
            print("Initializing git repo")
            self.repo = git.Repo.init(self.repo_dir)
        else:
            self.repo = git.Repo(self.repo_dir)

        # get public key of controller instance
        public_key_process = subprocess.run(
            [
                "ssh-keygen",
                "-y",
                "-f",
                global_settings.PROJECT_PATH / "id_thymis",
                "-P",
                "",
            ],
            capture_output=True,
            text=True,
        )

        if public_key_process.returncode != 0:
            logger.error("Failed to get public key: %s", public_key_process.stderr)
            self.public_key = None
        else:
            self.public_key = public_key_process.stdout.strip()

        # create a state, if not exists
        state_path = self.repo_dir / "state.json"
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

        logger.debug("Initializing known_hosts file")
        self.known_hosts_path = None
        self.update_known_hosts(db_session)

    def read_state(self):
        with open(self.repo_dir / "state.json", "r", encoding="utf-8") as f:
            state_json = f.read()
        state = State.model_validate_json(state_json)
        return state

    def write_state_and_reload(self, state: State):
        with open(self.repo_dir / "state.json", "w", encoding="utf-8") as f:
            f.write(state.model_dump_json(indent=2))
        # write a flake.nix
        repositories = BUILTIN_REPOSITORIES | state.repositories
        with open(self.repo_dir / "flake.nix", "w+", encoding="utf-8") as f:
            f.write(render_flake_nix(repositories))
        self.repo.git.add(".")
        # write missing flake.lock entries using nix flake lock
        subprocess.run(
            ["nix", *NIX_CMD[1:], "flake", "lock"], cwd=self.repo_dir, check=True
        )
        self.set_repositories_in_python_path(self.repo_dir, state)
        # create modules folder if not exists
        modules_path = self.repo_dir / "modules"
        del_path(modules_path)
        modules_path.mkdir(exist_ok=True)
        # create and empty hosts, tags folder
        del_path(self.repo_dir / "hosts")
        del_path(self.repo_dir / "tags")
        (self.repo_dir / "hosts").mkdir(exist_ok=True)
        (self.repo_dir / "tags").mkdir(exist_ok=True)
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

    def reload_from_disk(self):
        self.write_state_and_reload(self.read_state())

    def create_folder_and_write_modules(
        self, base_path: str, identifier: str, modules, priority
    ):
        path = self.repo_dir / base_path / identifier
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

    def commit(self, message: str):
        self.repo.git.add(".")
        try:
            if self.repo.index.diff("HEAD"):
                self.repo.index.commit(message)
                logger.info("Committed changes: %s", message)
        except git.BadName:
            self.repo.index.commit(message)

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
        except Exception:
            traceback.print_exc()
            return []

    def update_known_hosts(self, db_session: sqlalchemy.orm.Session):
        if not self.known_hosts_path or not self.known_hosts_path.exists():
            self.known_hosts_path = pathlib.Path(
                tempfile.NamedTemporaryFile(delete=False).name
            )

        deployment_infos = crud.deployment_info.get_all(db_session)
        with open(self.known_hosts_path, "w", encoding="utf-8") as f:
            for di in deployment_infos:
                if di.reachable_deployed_host and di.ssh_public_key:
                    f.write(f"{di.reachable_deployed_host} {di.ssh_public_key}\n")

        logger.debug("Updated known_hosts file at %s", self.known_hosts_path)

    def revert_commit(self, commit: str):
        commit_to_revert = self.repo.commit(commit)
        sha1 = self.repo.git.rev_parse(commit_to_revert.hexsha, short=True)
        self.repo.git.rm("-r", ".")
        self.repo.git.checkout(commit_to_revert.hexsha, ".")
        self.repo.index.commit(f"Revert to {sha1}: {commit_to_revert.message}")
        logger.info(f"Reverted commit: {commit_to_revert}")

    def get_remotes(self):
        return [history.Remote(name=r.name, url=r.url) for r in self.repo.remotes]

    def create_update_task(
        self, task_controller: "task.TaskController", db_session: sqlalchemy.orm.Session
    ):
        return task_controller.submit(
            models.task.ProjectFlakeUpdateTaskSubmission(
                project_path=str(self.path),
            ),
            db_session,
        )

    def verify_ssh_host_key_and_creds(
        self,
        host: str,
        public_key: str,
        port: int = 22,
        username: str = "root",
        pkey: paramiko.PKey = None,
    ):
        class ExpectedHostKeyNotFound(Exception):
            pass

        class CheckForExpectedHostKey(paramiko.MissingHostKeyPolicy):
            def __init__(self, expected_key):
                self.expected_key = expected_key

            def missing_host_key(self, client, hostname, key: paramiko.PKey):
                actual_key = f"{key.get_name()} {key.get_base64()}"
                if actual_key != self.expected_key:
                    raise ExpectedHostKeyNotFound()

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(CheckForExpectedHostKey(public_key))
        try:
            client.connect(
                hostname=host,
                port=port,
                username=username,
                pkey=pkey,
            )
        except ExpectedHostKeyNotFound:
            logger.error("Host key mismatch for %s", host)
            return False
        except paramiko.AuthenticationException:
            logger.error("Authentication failed for %s", host)
            return False
        except paramiko.SSHException as e:
            logger.error("SSH error for %s: %s", host, e)
            return False

        # run a command to verify the connection
        etc_os_release = client.exec_command("cat /etc/os-release")[1].read()
        logger.debug("Remote /etc/os-release: %s", etc_os_release)

        client.close()
        logger.debug("Verified host key for %s", host)

        return True
