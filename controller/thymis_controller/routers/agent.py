import logging

from fastapi import APIRouter, HTTPException, Request
from thymis_controller import crud, models
from thymis_controller.dependencies import ProjectAD, SessionAD
from thymis_controller.utils import determine_first_host_with_key

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register")
def register(
    register_request: models.RegisterDeviceRequest,
    request: Request,
    db_session: SessionAD,
    project: ProjectAD,
):
    # TODO verify authenticity of device in general (only permitted devices)

    # TODO verify authenticity of device of its key pair

    # check if device is already registered
    # check if the devive is present in the hostkey table
    # if yes, abort registration
    if crud.deployment_info.check_if_ssh_public_key_exists(
        db_session, register_request.public_key
    ):
        logging.info(
            f"Device with public key {register_request.public_key} is already registered"
        )
        raise HTTPException(status_code=400, detail="Your device is already registered")

    # TODO check if we can map the device to the Nix repository

    # check if device is reachable
    reachable_deployed_host: str | None = determine_first_host_with_key(
        hosts=[request.client.host, *register_request.ip_addresses],
        public_key=register_request.public_key,
    )

    # create deployment info
    deployment_info = crud.deployment_info.create(
        db_session,
        register_request.public_key,
        register_request.commit_hash,
        register_request.config_id,
        reachable_deployed_host=reachable_deployed_host,
    )

    # check if device is registered in hardware_device table
    crud.hardware_device.create_or_update(
        db_session, register_request.hardware_id, deployment_info.id
    )


@router.post("/heartbeat")
def heartbeat(
    heartbeat: models.DeviceHeartbeatRequest,
    db_session: SessionAD,
    request: Request,
):
    # check if device is registered
    device = crud.hostkey.get_by_public_key(db_session, heartbeat.public_key)
    if not device:
        logging.info(f"Device with public key {heartbeat.public_key} is not registered")
        raise HTTPException(status_code=404, detail="Your device is not registered")

    logging.debug(f"Device with identifier {device.identifier} sends heartbeat")
    # check for reachable device
    device_host = determine_first_host_with_key(
        hosts=[request.client.host, *heartbeat.ip_addresses],
        public_key=heartbeat.public_key,
    )

    if not device_host:
        logging.error(f"Device with identifier {device.identifier} is not reachable")
        raise HTTPException(status_code=400, detail="Your device is not reachable")

    if device.device_host != device_host:
        logging.info(
            f"Device with identifier {device.identifier} has new host {device_host}"
        )
        device.device_host = device_host
        db_session.commit()
