import logging

import paramiko
from fastapi import APIRouter, HTTPException, Request
from thymis_controller import crud, models
from thymis_controller.config import global_settings
from thymis_controller.dependencies import ProjectAD, SessionAD
from thymis_controller.nix import check_device_reference
from thymis_controller.utils import determine_first_host_with_key

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/notify")
def device_notify(
    device_notify_request: models.DeviceNotifyRequest,
    request: Request,
    db_session: SessionAD,
    project: ProjectAD,
):
    request_source = (
        request.client
    )  # see --forwarded-allow-ips for uvicorn configuration
    logger.debug(
        "Device with public key %s notifies controller with commit hash %s and config id %s from %s",
        device_notify_request.public_key,
        device_notify_request.commit_hash,
        device_notify_request.config_id,
        request_source.host,
    )
    if (
        device_notify_request.commit_hash and device_notify_request.config_id
    ) and not check_device_reference(
        project.repo_dir,
        device_notify_request.commit_hash,
        device_notify_request.config_id,
    ):
        logger.error(
            "Device with public key %s notifies controller with commit hash %s and "
            "config id %s which is not a valid reference to the project at %s",
            device_notify_request.public_key,
            device_notify_request.commit_hash,
            device_notify_request.config_id,
            project.repo_dir,
        )
        raise HTTPException(
            status_code=400
        )  # do not reveal information to misbehaving devices

    # check if device is reachable using device supplied public key
    reachable_deployed_host: str | None = determine_first_host_with_key(
        hosts=[request.client.host, *device_notify_request.ip_addresses],
        public_key=device_notify_request.public_key,
    )

    # verify ssh key
    verified_ssh = project.verify_ssh_host_key_and_creds(
        reachable_deployed_host,
        device_notify_request.public_key,
        port=22,
        username="root",
        pkey=paramiko.PKey.from_path(global_settings.PROJECT_PATH / "id_thymis"),
    )

    if not verified_ssh:
        logger.error(
            "Device with public key %s notifies controller with commit hash %s and "
            "config id %s from %s with unreachable host %s",
            device_notify_request.public_key,
            device_notify_request.commit_hash,
            device_notify_request.config_id,
            request_source.host,
            reachable_deployed_host,
        )
        raise HTTPException(status_code=400)

    hardware_ids = {
        key: value for key, value in device_notify_request.hardware_ids.items() if value
    }
    # check: does any of my hardware ids overlap with any in the db
    overlapping_devices = crud.hardware_device.find_overlapping_hardware_ids(
        db_session, hardware_ids
    )

    # count the number of overlapping devices
    overlapping_devices_count = len(overlapping_devices)
    if overlapping_devices_count >= 2:
        # fail for now
        logger.error(
            "Device with public key %s notifies controller with hardware ids %s which overlap with %d devices",
            device_notify_request.public_key,
            hardware_ids,
            overlapping_devices_count,
        )
        logger.error(
            "Overlapping devices: %s",
            overlapping_devices,
        )
        raise HTTPException(status_code=400)

    # count has to be 0 or 1, both are fine

    # current state: device is reachable via ssh and has a valid public key
    # identity of the hardware device is either completely new or already known, but not overlapping with multiple devices

    # now: check wether any other deployment_info has the same public key
    same_public_key = crud.deployment_info.get_by_ssh_public_key(
        db_session, device_notify_request.public_key
    )

    # if more than 2 devices have the same public key, fail
    if len(same_public_key) >= 2:
        logger.error(
            "Device with public key %s notifies controller with commit hash %s and "
            "config id %s from %s with public key that is already in use by %d devices"
            "we do not handle this case yet",
            device_notify_request.public_key,
            device_notify_request.commit_hash,
            device_notify_request.config_id,
            request_source.host,
            len(same_public_key),
        )
        raise HTTPException(status_code=400)

    force_pubkey_update = len(same_public_key) == 1 and not overlapping_devices

    if force_pubkey_update:
        logger.info("Force public key update for device %s", reachable_deployed_host)
        return {"force_pubkey_update": True}

    # create or update deployment_info
    deployment_info = crud.deployment_info.create_or_update_by_public_key(
        db_session,
        device_notify_request.public_key,
        device_notify_request.commit_hash,
        device_notify_request.config_id,
        reachable_deployed_host,
    )
    hardware_device = crud.hardware_device.create_or_update(
        db_session,
        hardware_ids,
        deployment_info.id,
    )

    project.update_known_hosts(db_session)

    return {"success": True}


@router.post("/register")
def device_register(request: Request):
    logger.warning(f"{request.client.host} calls deprecated /agent/register endpoint")
    raise HTTPException(
        status_code=404, detail="The /agent/register endpoint is deprecated"
    )


@router.post("/heartbeat")
def device_heartbeat(request: Request):
    logger.warning(f"{request.client.host} calls deprecated /agent/heartbeat endpoint")
    raise HTTPException(
        status_code=404, detail="The /agent/heartbeat endpoint is deprecated"
    )
