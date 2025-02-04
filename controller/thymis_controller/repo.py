import datetime
import logging
import pathlib
import subprocess

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Commit(BaseModel):
    SHA: str
    SHA1: str
    message: str
    date: datetime.datetime
    author: str
    state_diff: list[str] = []


class Repo:
    def __init__(self, path: pathlib.Path):
        self.path = path
        self.init()

    def init(self):
        self.path.mkdir(exist_ok=True, parents=True)

        if not (self.path / ".git").exists():
            logger.info(f"Initializing git repository at {self.path}")
            subprocess.run(["git", "init", "-b", "master"], cwd=self.path)

    def add(self, *files: pathlib.Path):
        logger.info(f"Adding files to git: {', '.join(files)}")
        subprocess.run(["git", "add", *files], cwd=self.path)

    def commit(self, message: str):
        logger.info(f"Committing changes to git: {message}")
        subprocess.run(["git", "commit", "-m", message], cwd=self.path)

    def history(self) -> Commit:
        try:
            result = subprocess.run(
                [
                    "git",
                    "rev-list",
                    "HEAD",
                    "--format='%H%x00%h%x00%s%x00%ci%x00%an'",
                    "--no-commit-header",
                ],
                cwd=self.path,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            logger.exception("Error getting git history")
            return []

        return [
            Commit(
                SHA=sha,
                SHA1=sha1,
                message=message,
                date=datetime.datetime.fromisoformat(date),
                author=author,
            )
            for line in result.stdout.splitlines()
            for sha, sha1, message, date, author in [line.split("\x00")]
        ]
