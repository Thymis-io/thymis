import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from thymis_controller import crud, models
from thymis_controller.dependencies import SessionAD, get_project
from thymis_controller.utils import determine_first_host_with_key

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register")
def register(
    register_request: models.RegisterDeviceRequest,
    request: Request,
    db_session: SessionAD,
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

    # differentiace between a device that is already registered and a device that is not
    if crud.hostkey.build_hash_is_registered(db_session, register_request.build_hash):
        # device is already registered
        logger.info(
            f"Device with build hash {register_request.build_hash} already registered. Creating new device."
        )

        # TODO create new device from JSON in image database model
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
        )
