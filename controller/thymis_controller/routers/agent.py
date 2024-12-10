import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from thymis_controller import crud, models
from thymis_controller.dependencies import ProjectAD, SessionAD
from thymis_controller.project import Project
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
    request_device_host = request.client.host
    logger.info(
        f"Device with host {request_device_host} from request and build hash {register_request.build_hash} attemps to register"
    )

    device_host = determine_first_host_with_key(
        hosts=[request_device_host, *register_request.ip_addresses],
        public_key=register_request.public_key,
    )

    if not device_host:
        logger.error(
            f"Device with host {request_device_host} from request and build hash {register_request.build_hash} is not reachable from the controller"
        )
        raise HTTPException(
            status_code=400, detail="Your device is not reachable from the controller"
        )

    # get device by build hash from image table
    image = crud.image.get_by_build_hash(db_session, register_request.build_hash)
    if not image:
        # device is not registered in the image database
        logger.error(
            f"Device with build hash {register_request.build_hash} is not registered in the image database"
        )
        raise HTTPException(status_code=400, detail="Your device is not registered")

    # idea: check if identifier from image entry has a corresponding entry in the hostkey table
    # differentiate between a device that is already registered and a device that is not
    if crud.hostkey.has_device(db_session, image.identifier):
        # device is already registered

        # check if agent build hash is newer than hostkey build hash
        hostkey = crud.hostkey.get_by_build_hash(
            db_session, register_request.build_hash
        )
        if hostkey:
            # registering device is the same as the one in the hostkey table -> clone device
            logger.info(
                f"Device with build hash {register_request.build_hash} already registered. Creating new device."
            )

            state = project.read_state()
            if not image.device_state:
                # device state is not present in the image
                logger.error(
                    f"Device with build hash {register_request.build_hash} does not have a device state. Cannot clone device."
                )

            device = models.Device.model_validate(
                image.device_state, from_attributes=True
            )
            # find new name
            x = 1
            device_name = lambda x: f"{image.identifier}-{x}"
            check_name = lambda x: any(
                device.identifier == device_name(x) for device in state.devices
            )
            while check_name(x):
                x += 1

            device.identifier = device_name(x)
            device.displayName = f"{device.displayName}-{x}"
            state.devices.append(device)
            project.write_state_and_reload(state)

            crud.hostkey.create(
                db_session,
                identifier=device.identifier,
                build_hash=register_request.build_hash,
                public_key=register_request.public_key,
                device_host=device_host,
                project=project,
            )
        else:
            # registering device is not the same as the one in the hostkey table, replacing device
            logger.info(
                f"Device with build hash {register_request.build_hash} already registered. Updating device."
            )
            state = project.read_state()

            origin_device = None
            for device in state.devices:
                if device.identifier == image.identifier:
                    origin_device = device
                    break
            else:
                logger.error(
                    f"Device with identifier {image.identifier} not found in state. Cannot replace device."
                )
                raise HTTPException(
                    status_code=500,
                    detail="Device not found in state. Cannot replace device. Internal Server Error.",
                )

            device = origin_device.model_copy()

            # find new name
            def device_name(x, text=image.identifier):
                if x == 0:
                    return f"{text}-old"
                return f"{text}-old-{x}"

            x = 0
            while any(device.identifier == device_name(x) for device in state.devices):
                x += 1

            device.identifier = device_name(x)
            device.displayName = device_name(x, text=device.displayName)
            state.devices.append(device)
            project.write_state_and_reload(state)

            crud.hostkey.rename_device(db_session, image.identifier, device.identifier)

            crud.hostkey.create(
                db_session,
                identifier=image.identifier,
                build_hash=register_request.build_hash,
                public_key=register_request.public_key,
                device_host=device_host,
                project=project,
            )

            # remove old hostkey, to prevent deploying to the old device
            # TODO maybe: invalidate instead of delete
            crud.hostkey.delete(db_session, device.identifier)
    else:
        # device is not registered
        logger.info(
            f"Device with build hash {register_request.build_hash} not registered. Registering device."
        )

        image = crud.image.get_by_build_hash(db_session, register_request.build_hash)
        if not image:
            # device is not registered in the image database
            logger.error(
                f"Device with build hash {register_request.build_hash} is not registered in the image database"
            )
            raise HTTPException(status_code=400, detail="Your device is not registered")

        # device is registered but not in the hostkey table
        crud.hostkey.create(
            db_session,
            identifier=image.identifier,
            build_hash=register_request.build_hash,
            public_key=register_request.public_key,
            device_host=device_host,
            project=project,
        )
    project.update_known_hosts(db_session)


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
