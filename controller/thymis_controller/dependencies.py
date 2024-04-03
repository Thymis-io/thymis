from fastapi import Depends
from thymis_controller.crud.project import Project, global_project


def get_or_init_project():
    if not global_project.is_initialized():
        global_project.initialize()

    return global_project


def get_or_init_state(project: Project = Depends(get_or_init_project)):
    return project.load_state_from_file()
