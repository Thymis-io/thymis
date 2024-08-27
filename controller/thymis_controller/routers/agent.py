import logging

from fastapi import APIRouter, HTTPException, Request
from thymis_controller import crud, models
from thymis_controller.dependencies import SessionAD

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register")
def register(
    register_request: models.RegisterDeviceRequest,
    request: Request,
    db_session: SessionAD,
):
    # TODO save ip
    device_host = request.client.host
    logger.info(
        f"Device with host {device_host} and build hash {register_request.build_hash} attemps to register"
    )

    if crud.hostkey.register_device(
        db_session,
        register_request.build_hash,
        register_request.public_key,
        device_host,
    ):
        logger.info(
            f"Device with build hash {register_request.build_hash} succesfully registered"
        )
        return {"message": "Device registered"}
    else:
        raise HTTPException(status_code=404, detail="Device not found")
