import os

from fastapi import Depends
from thymis_controller.project import Project

if os.getenv("REPO_PATH"):
    REPO_PATH = os.getenv("REPO_PATH")
else:
    REPO_PATH = "/var/lib/thymis"
    print(f"REPO_PATH not set. Using default path: {REPO_PATH}")

global_project = Project(REPO_PATH)


def get_project():
    return global_project


def get_state(project: Project = Depends(get_project)):
    return project.read_state()
