from sqlalchemy.orm import Session
from thymis_controller import db_models


def create(
    session: Session,
    ssh_public_key: str,
    deployed_config_commit: str,
    deployed_config_id: str,
    reachable_deployed_host: str | None = None,
) -> db_models.DeploymentInfo:
    new_deployment_info = db_models.DeploymentInfo(
        ssh_public_key=ssh_public_key,
        deployed_config_commit=deployed_config_commit,
        deployed_config_id=deployed_config_id,
        reachable_deployed_host=reachable_deployed_host,
    )
    session.add(new_deployment_info)
    session.commit()
    session.refresh(new_deployment_info)
    return new_deployment_info


def get_by_id(session: Session, id: str) -> db_models.DeploymentInfo | None:
    return (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.id == id)
        .first()
    )


def check_if_ssh_public_key_exists(session: Session, ssh_public_key: str) -> bool:
    return (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.ssh_public_key == ssh_public_key)
        .first()
        is not None
    )


def get_all(session: Session):
    return session.query(db_models.DeploymentInfo).all()


def get_device_host_by_config_id(session: Session, config_id: str) -> str | None:
    di = (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.deployed_config_id == config_id)
        .first()
    )
    return di.reachable_deployed_host if di else None


def get_by_config_id(
    session: Session, config_id: str
) -> db_models.DeploymentInfo | None:
    return (
        session.query(db_models.DeploymentInfo)
        .filter(db_models.DeploymentInfo.deployed_config_id == config_id)
        .first()
    )
