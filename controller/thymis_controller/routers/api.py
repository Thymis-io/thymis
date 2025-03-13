import logging

from fastapi import APIRouter, Depends
from thymis_controller.dependencies import require_valid_user_session
from thymis_controller.routers import (
    api_action,
    api_artifacts,
    api_deployment_info,
    api_secrets,
    api_state,
    api_statistics,
    api_task,
    api_ui_sockets,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(require_valid_user_session)],
)

router.include_router(api_artifacts.router)
router.include_router(api_task.router)
router.include_router(api_secrets.router)
router.include_router(api_state.router)
router.include_router(api_action.router)
router.include_router(api_deployment_info.router)
router.include_router(api_ui_sockets.router)
router.include_router(api_statistics.router)
