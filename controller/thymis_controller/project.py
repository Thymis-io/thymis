import datetime
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
import uuid
from typing import TYPE_CHECKING

import sqlalchemy
import sqlalchemy.orm
from pyrage import decrypt, encrypt, passphrase, ssh
from thymis_controller import crud, db_models, migration, models
from thymis_controller.config import global_settings
from thymis_controller.models.external_repo import ExternalRepoStatus
from thymis_controller.models.state import State
from thymis_controller.nix import NIX_CMD, get_input_out_path
from thymis_controller.nix.log_parse import NixParser
from thymis_controller.nix.templating import render_flake_nix
from thymis_controller.notifications import NotificationManager
from thymis_controller.repo import Repo
from thymis_controller.task import controller as task

if TYPE_CHECKING:
    from thymis_controller import modules

logger = logging.getLogger(__name__)

if "THYMIS_FLAKE_ROOT" in os.environ:
    thymis_repo = models.Repo(
        url=f"git+file://{pathlib.Path(os.environ['THYMIS_FLAKE_ROOT']).resolve()}"
    )
else:
    thymis_repo = models.Repo(url="github:thymis-io/thymis/v0.6")


BUILTIN_REPOSITORIES = {
    "thymis": thymis_repo,
    "nixpkgs": models.Repo(follows="thymis/nixpkgs"),
}

HOST_PRIORITY = 80


def del_path(path: os.PathLike):
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink()


startup_python_path = sys.path.copy()


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
    repo: Repo
    notification_manager: NotificationManager
    known_hosts_path: pathlib.Path
    public_key: str
    state_lock = threading.Lock()
    write_repo_lock = threading.Lock()
    repo_dir: pathlib.Path
    controller_age_identity: ssh.Identity
    controller_age_recipient: ssh.Recipient
    lockfile: str | None = None
    external_repo_status: dict[str, ExternalRepoStatus] = {}

    def __init__(
        self,
        path,
        notification_manager: NotificationManager,
        db_session: sqlalchemy.orm.Session,
    ):
        self.path = pathlib.Path(path)
        self.notification_manager = notification_manager
        # create the path if not exists
        self.path.mkdir(exist_ok=True, parents=True)
        self.repo_dir = self.path / "repository"
        self.repo = Repo(self.repo_dir, self.notification_manager)

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
            check=True,
        )

        if public_key_process.returncode != 0:
            logger.error("Failed to get public key: %s", public_key_process.stderr)
            self.public_key = None
        else:
            self.public_key = public_key_process.stdout.strip()

        # get age identity
        with open(global_settings.PROJECT_PATH / "id_thymis", "rb") as f:
            controller_age = ssh.Identity.from_buffer(
                f.read(),
            )
        self.controller_age_identity = controller_age
        self.controller_age_recipient = ssh.Recipient.from_str(self.public_key)

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

        if not self.repo.has_root_commit():
            self.repo.add(".")
            self.repo.commit("Initial commit")
        self.repo.start_file_watcher()

        logger.debug("Initializing known_hosts file")
        self.known_hosts_path = None
        self.update_known_hosts(db_session)

    def encrypt(self, data: bytes) -> bytes:
        return encrypt(data, [self.controller_age_recipient])

    def decrypt(self, data: bytes) -> bytes:
        return decrypt(data, [self.controller_age_identity])

    def _process_secret(
        self, value: bytes, processing_type: db_models.SecretProcessingTypes
    ) -> bytes:
        """
        Process a secret value according to the specified processing type.

        Args:
            value: The raw secret value to process
            processing_type: The type of processing to apply

        Returns:
            Processed secret value as bytes
        """
        if processing_type == db_models.SecretProcessingTypes.NONE:
            return value

        if processing_type == db_models.SecretProcessingTypes.MKPASSWD_YESCRYPT:
            try:
                # Use mkpasswd to hash the password with yescrypt
                result = subprocess.run(
                    ["mkpasswd", "--method=yescrypt", "--stdin"],
                    input=value,
                    capture_output=True,
                    check=True,
                    text=False,  # Keep as bytes
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                logger.error(f"mkpasswd failed: {e}")
                logger.error(f"stderr: {e.stderr}")
                # Return the original value if processing fails
                return value

        # Fallback for any unhandled types
        logger.warning(f"Unhandled processing type: {processing_type}")
        return value

    def get_processed_secrets(
        self,
        db_session: sqlalchemy.orm.Session,
        secret_ids: list[uuid.UUID],
        recipient: ssh.Recipient | str,
    ) -> dict[uuid.UUID, bytes]:
        # decrypt, process, encrypt
        secrets = crud.secrets.get_by_ids(db_session, secret_ids)
        processed_secrets = {}
        for secret in secrets:
            value = self.decrypt(secret.value_enc)
            value = self._process_secret(value, secret.processing_type)
            if isinstance(recipient, str):
                value = passphrase.encrypt(value, recipient)
            else:
                value = encrypt(value, [recipient])
            processed_secrets[secret.id] = value
        return processed_secrets

    def create_secret(
        self,
        db_session: sqlalchemy.orm.Session,
        display_name: str,
        secret_type: db_models.SecretTypes,
        value: bytes,
        filename: str | None = None,
        include_in_image: bool = False,
        processing_type: db_models.SecretProcessingTypes = db_models.SecretProcessingTypes.NONE,
    ) -> db_models.Secret:
        # encrypt the value and save it to the database
        value_size = len(value)
        value_enc = self.encrypt(value)
        secret = crud.secrets.create(
            db_session,
            display_name,
            secret_type,
            value_enc,
            value_size,
            filename,
            include_in_image,
            processing_type,
        )
        return secret

    def get_all_secrets(
        self,
        db_session: sqlalchemy.orm.Session,
    ) -> dict[uuid.UUID, models.SecretShort]:
        # get all secrets from the database
        secrets = crud.secrets.get_all_secrets(db_session)
        return {
            secret.id: models.SecretShort.from_orm_secret(secret, self.decrypt)
            for secret in secrets
        }

    def get_secret(
        self,
        db_session: sqlalchemy.orm.Session,
        secret_id: uuid.UUID,
    ) -> models.SecretShort | None:
        # get a secret from the database
        secret = crud.secrets.get_by_id(db_session, secret_id)
        return (
            models.SecretShort.from_orm_secret(secret, self.decrypt) if secret else None
        )

    def update_secret(
        self,
        db_session: sqlalchemy.orm.Session,
        secret_id: uuid.UUID,
        display_name: str | None = None,
        secret_type: db_models.SecretTypes | None = None,
        value: bytes | None = None,
        filename: str | None = None,
        include_in_image: bool | None = None,
        processing_type: db_models.SecretProcessingTypes | None = None,
    ) -> models.SecretShort | None:
        # encrypt the value and save it to the database
        if value:
            value_size = len(value)
            value_enc = self.encrypt(value)
        else:
            value_size = None
            value_enc = None
        secret = crud.secrets.update(
            db_session,
            secret_id,
            display_name,
            secret_type,
            value_enc,
            value_size,
            filename,
            include_in_image,
            processing_type,
        )
        return (
            models.SecretShort.from_orm_secret(secret, self.decrypt) if secret else None
        )

    def delete_secret(
        self,
        db_session: sqlalchemy.orm.Session,
        secret_id: uuid.UUID,
    ) -> bool:
        return crud.secrets.delete(db_session, secret_id)

    def download_secret_file(
        self,
        db_session: sqlalchemy.orm.Session,
        secret_id: uuid.UUID,
        apply_processing: bool = True,
    ) -> tuple[bytes, str] | None:
        secret = crud.secrets.get_by_id(db_session, secret_id)
        if not secret:
            return None
        # assert
        if not secret.filename and (not secret.type == db_models.SecretTypes.FILE):
            return None
        # decrypt the value
        value = self.decrypt(secret.value_enc)

        # Apply processing if requested
        if apply_processing:
            value = self._process_secret(value, secret.processing_type)

        return value, secret.filename

    def has_lockfile_changed(self, flake_path):
        lockfile_path = os.path.join(flake_path, "flake.lock")
        try:
            with open(lockfile_path, "r", encoding="utf-8") as f:
                new_lockfile = f.read()
        except FileNotFoundError:
            logger.error("No flake.lock found at %s", lockfile_path)
            new_lockfile = None
        if new_lockfile == self.lockfile:
            return False
        self.lockfile = new_lockfile
        return True

    def load_repositories(self, repositories: dict[str, models.Repo]):
        from thymis_controller import modules

        if not self.has_lockfile_changed(self.repo_dir):
            return
        # for each repository: get_input_out_path from the flake.nix in the path
        input_out_paths = {}
        for input_name, repo in repositories.items():
            self.external_repo_status[input_name] = ExternalRepoStatus(status="loading")
            if not repo.url:
                self.external_repo_status[input_name].status = "no-url"
                continue
            path, error_msg = get_input_out_path(self.repo_dir, input_name)
            if path is None:
                self.external_repo_status[input_name].status = "no-path"
                self.external_repo_status[input_name].details = error_msg
                continue
            # check wether path / README.md exists and contains the string "contains thymis modules"
            if not os.path.exists(os.path.join(path, "README.md")):
                logger.debug("Repository %s does not contain a README.md", input_name)
                logger.debug("Skipping %s", input_name)
                self.external_repo_status[input_name].status = "no-readme"
                continue
            with open(os.path.join(path, "README.md"), "r", encoding="utf-8") as f:
                if "contains thymis modules" not in f.read():
                    logger.debug("Repository %s contains no thymis modules", input_name)
                    logger.debug("Skipping %s", input_name)
                    self.external_repo_status[input_name].status = "no-magic-string"
                    continue
            logger.info("Found repository %s at %s", input_name, path)
            input_out_paths[input_name] = path
        self.notification_manager.broadcast_invalidate_notification(
            ["/api/external-repositories/status"]
        )
        # add the paths to sys.path
        sys.path = startup_python_path.copy()
        # for path in input_out_paths.values():
        importlib.invalidate_caches()
        modules_found = []
        for input_name, path in input_out_paths.items():
            logger.debug("Adding %s at %s to sys.path", input_name, path)
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
                            self.external_repo_status[input_name].modules.append(
                                module_obj.type
                            )
                    self.external_repo_status[input_name].status = "loaded"
                except Exception as e:  # pylint: disable=broad-except
                    traceback.print_exc()
                    logger.error("Error while importing module %s: %s", module.name, e)
        modules.ALL_MODULES = modules.ALL_MODULES_START.copy()
        modules.ALL_MODULES.extend(modules_found)
        self.notification_manager.broadcast_invalidate_notification(
            ["/api/external-repositories/status"]
        )

    def read_state(self):
        with self.state_lock:
            with open(self.repo_dir / "state.json", "r", encoding="utf-8") as f:
                state_json = f.read()
            state = State.model_validate_json(state_json)
            return state

    def write_state(self, state: State):
        with self.state_lock:
            with open(self.repo_dir / "state.json", "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))

    def write_state_and_reload(self, state: State):
        self.write_state(state)
        self.reload_state(state)

    def reload_state(self, state: State):
        with self.write_repo_lock:
            self._reload_state_unsafe(state)

    def _reload_state_unsafe(self, state: State):
        """
        This method must always be called within a write_repo_lock to prevent race conidtions
        """
        error = None
        self.repo.pause_file_watcher()
        repositories = self.check_healthy_repositories(state)
        if (self.repo_dir / "flake.nix").exists():
            with open(self.repo_dir / "flake.nix", "r", encoding="utf-8") as f:
                flake_nix_content = f.read()
        else:
            flake_nix_content = ""
        new_flake_nix_content = render_flake_nix(repositories)
        if flake_nix_content != new_flake_nix_content:
            logger.info("Updating flake.nix content")
            with open(self.repo_dir / "flake.nix", "w+", encoding="utf-8") as f:
                f.write(new_flake_nix_content)
            self.repo.add(".")
            # write missing flake.lock entries using nix flake lock
            try:
                logger.info("Running nix flake lock...")
                start_time = datetime.datetime.now()
                subprocess.run(
                    ["nix", *NIX_CMD[1:], "flake", "lock", "--allow-dirty-locks"],
                    cwd=self.repo_dir,
                    capture_output=True,
                    check=True,
                )
                logger.info(
                    "Successfully ran nix flake lock in %s",
                    datetime.datetime.now() - start_time,
                )
            except subprocess.CalledProcessError as e:
                logger.error("Error while running nix flake lock: %s", e)
                logger.error("stdout: %s", e.stdout)
                logger.error("stderr: %s", e.stderr)
                traceback.print_exc()
                error = e
        self.load_repositories(repositories)
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
        for config in state.configs:
            # assert device.identifier, "identifier cannot be empty"
            if not config.identifier:
                logger.info("Device with empty identifier found, skipping")
                continue
            self.create_folder_and_write_modules(
                "hosts", config.identifier, config.modules, HOST_PRIORITY
            )
        for tag in state.tags:
            self.create_folder_and_write_modules(
                "tags", tag.identifier, tag.modules, tag.priority
            )
        self.repo.add(".")
        self.repo.resume_file_watcher()
        self.notification_manager.broadcast_invalidate_notification(
            ["/api/repo_status"]
        )
        if error:
            raise error

    def check_healthy_repositories(self, state: State):
        repositories = BUILTIN_REPOSITORIES | state.repositories
        healthy_repos = {}
        for name, repo in repositories.items():
            if not repo.url:
                continue
            try:
                subprocess.run(
                    ["nix", *NIX_CMD[1:], "flake", "prefetch", repo.url],
                    capture_output=True,
                    check=True,
                )
                healthy_repos[name] = repo
            except subprocess.CalledProcessError as e:
                nix_parser = NixParser()
                nix_parser.process_buffer(bytearray(e.stderr))
                self.external_repo_status[name] = ExternalRepoStatus(
                    status="no-path", details=nix_parser.msg_output
                )
                continue
        return healthy_repos

    def reload_from_disk(self):
        self.write_state_and_reload(self.read_state())

    def create_folder_and_write_modules(
        self, base_path: str, identifier: str, modules, priority
    ):
        path = self.repo_dir / base_path / identifier
        path.mkdir(exist_ok=True, parents=True)
        with open(path / ".gitkeep", mode="a", encoding="utf-8"):
            pass
        for module_settings in modules:
            try:
                module = get_module_class_instance_by_type(module_settings.type)
                module.write_nix(path, module_settings, priority, self)
            except Exception as e:
                logger.error(
                    "Error while writing module %s: %s", module_settings.type, e
                )
                traceback.print_exc()

    def get_modules_for_config(
        self, state: State, config: models.Config
    ) -> list[tuple["modules.Module", models.ModuleSettings]]:
        module_pairs = []  # module, modules_setting pair
        for module_settings in config.modules:
            try:
                module = get_module_class_instance_by_type(module_settings.type)
                module_pairs.append((module, module_settings))
            except Exception as e:
                logger.error(
                    "Error while getting module %s: %s", module_settings.type, e
                )
                traceback.print_exc()
        for tag in state.tags:
            if tag.identifier in config.tags:
                for module_settings in tag.modules:
                    try:
                        module = get_module_class_instance_by_type(module_settings.type)
                        module_pairs.append((module, module_settings))
                    except Exception as e:
                        logger.error(
                            "Error while getting module %s: %s", module_settings.type, e
                        )
                        traceback.print_exc()
        return module_pairs

    def clear_history(self, db_session: sqlalchemy.orm.Session):
        if "RUNNING_IN_PLAYWRIGHT" in os.environ:
            with self.write_repo_lock:
                # reinits the git repo
                self.repo.stop_file_watcher()
                shutil.rmtree(self.repo_dir)
                self.repo = Repo(self.repo_dir, self.notification_manager)
                state = State()
                self.write_state(state)
                self._reload_state_unsafe(state)
                if not self.repo.has_root_commit():
                    self.repo.add(".")
                    self.repo.commit("Initial commit")
                self.repo.start_file_watcher()
                self.update_known_hosts(db_session)

    def clear_images(self):
        logger.info("Clearing images and image-builders directories")
        del_path(self.path / "images")
        del_path(self.path / "image-builders")

    def update_known_hosts(self, db_session: sqlalchemy.orm.Session):
        if not self.known_hosts_path or not self.known_hosts_path.exists():
            self.known_hosts_path = pathlib.Path(
                tempfile.NamedTemporaryFile(delete=False).name
            )
        with open(self.known_hosts_path, "w", encoding="utf-8") as f:
            deployment_infos = crud.deployment_info.get_all(db_session)
            for di in deployment_infos:
                if di.reachable_deployed_host and di.ssh_public_key:
                    f.write(f"{di.reachable_deployed_host} {di.ssh_public_key}\n")

        logger.debug("Updated known_hosts file at %s", self.known_hosts_path)

    def create_update_task(
        self,
        task_controller: "task.TaskController",
        user_session_id: uuid.UUID,
        db_session: sqlalchemy.orm.Session,
    ):
        return task_controller.submit(
            models.task.ProjectFlakeUpdateTaskSubmission(
                project_path=str(self.path),
            ),
            user_session_id=user_session_id,
            db_session=db_session,
        )
