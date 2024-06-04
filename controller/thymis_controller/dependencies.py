import logging
import os

logger = logging.getLogger(__name__)


from fastapi import Depends
from thymis_controller.project import Project

global_project = None


def get_project():
    global global_project
    if global_project is None:
        if os.getenv("REPO_PATH"):
            REPO_PATH = os.getenv("REPO_PATH")
        else:
            REPO_PATH = "/var/lib/thymis"
            logger.warning("REPO_PATH not set. Using default path: %s", REPO_PATH)

        global_project = Project(REPO_PATH)
    return global_project


def get_state(project: Project = Depends(get_project)):
    return project.read_state()
