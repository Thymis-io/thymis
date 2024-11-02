import logging
import os
import pathlib
import threading
import traceback

import git
from thymis_controller import models
from thymis_controller.notifications import notification_manager

logger = logging.getLogger(__name__)
history_lock = threading.Lock()


class Repo:
    repo: git.Repo

    def __init__(self, path: pathlib.Path) -> None:
        path.mkdir(exist_ok=True, parents=True)

        if not (path / ".git").exists():
            print("Initializing git repo at", path)
            self.repo = git.Repo.init(path)
        else:
            print("Loading git repo from", path)
            self.repo = git.Repo(path)

    def info(self):
        active_branch = self.repo.active_branch
        tracking_branch = active_branch.tracking_branch()

        if tracking_branch:
            try:
                ahead = self._ahead_count(tracking_branch.name, active_branch.name)
                behind = self._ahead_count(active_branch.name, tracking_branch.name)
            except:
                traceback.print_exc()
                ahead = 0
                behind = 0
        else:
            ahead = 0
            behind = 0

        return models.history.GitInfo(
            active_branch=self.repo.active_branch.name,
            remote_branch=tracking_branch.name if tracking_branch else None,
            ahead=ahead,
            behind=behind,
            remotes=self.remotes(),
        )

    def stage_all(self):
        self.repo.git.add(".")

    def commit(self, summary: str):
        self.stage_all()
        self._commit(summary)
        self.pull()
        self.push()

    def push(self):
        try:
            self.repo.git.push()
        except git.GitCommandError as e:
            traceback.print_exc()
            notification_manager.broadcast(self._git_command_error_message(e))

    def pull(self):
        self.fetch_all()

        if not self.repo.head.is_valid() or not self.info().remote_branch:
            return

        try:
            # fail if git askings for credentials to avoid blocking
            os.environ["GIT_TERMINAL_PROMPT"] = "0"
            self.repo.git.pull("--ff-only")
        except git.GitCommandError as e:
            traceback.print_exc()
            stderr = e.stderr.replace("hint:", "\t").replace("\n\t\n", "\n")
            if "terminal prompts disabled" in stderr:
                remote = self.info().remote_branch
                message = f"Failed to pull from git remote {remote}: repository not found or credentials missing"
            else:
                message = self._git_command_error_message(e)
            notification_manager.broadcast(message)

    def fetch_all(self):
        try:
            self.repo.git.fetch("--all", "--prune")
        except git.GitCommandError as e:
            traceback.print_exc()
            notification_manager.broadcast(str(e))

    def hexsha(self):
        return self.repo.head.object.hexsha

    def history(self):
        try:
            with history_lock:
                if not self.repo.head.is_valid():
                    return []

                return [
                    models.history.Commit(
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

    def revert_commit(self, commit: str):
        commit_to_revert = self.repo.commit(commit)
        sha1 = self.repo.git.rev_parse(commit_to_revert.hexsha, short=True)
        self.repo.git.rm("-r", ".")
        self.repo.git.checkout(commit_to_revert.hexsha, ".")
        self.repo.index.commit(f"Revert to {sha1}: {commit_to_revert.message}")
        logger.info(f"Reverted commit: {commit_to_revert}")

    def remotes(self):
        return [
            models.history.Remote(
                name=remote.name,
                url=remote.url,
                branches=[ref.name for ref in remote.refs],
            )
            for remote in self.repo.remotes
        ]

    def has_remote(self, name: str):
        return name in [remote.name for remote in self.repo.remotes]

    def add_remote(self, remote: models.history.UpdateRemote):
        self.repo.create_remote(remote.name, remote.url)

    def update_remote(
        self,
        name: str,
        remote_update: models.history.UpdateRemote,
    ):
        if name != remote_update.name:
            self.repo.git.remote("rename", name, remote_update.name)
        if self.repo.remote(remote_update.name).url != remote_update.url:
            self.repo.git.remote("set-url", remote_update.name, remote_update.url)
        self.pull()

    def switch_remote_branch(self, branch: str):
        try:
            self.repo.git.reset("--hard")
            local_branch = branch.split("/", 1)[-1]
            self.repo.git.switch("-C", local_branch, branch)
        except git.GitCommandError as e:
            traceback.print_exc()
            notification_manager.broadcast(str(e))

        self.pull()

    def delete_remote(self, name: str):
        self.repo.delete_remote(name)

    def _ahead_count(self, from_ref: str, to_ref: str):
        return self.repo.git.rev_list(f"{from_ref}..{to_ref}", count=True)

    def _commit(self, summary: str):
        try:
            if self.repo.index.diff("HEAD"):
                self.repo.index.commit(summary)
                logger.info("Committed changes: %s", summary)
        except git.BadName:
            self.repo.index.commit(summary)

    def _git_command_error_message(self, e: git.GitCommandError):
        stderr = e.stderr.replace("hint:", "\t").replace("\n\t\n", "\n")
        return f"{' '.join(e.command)} failed with status code {e.status}{stderr}"
