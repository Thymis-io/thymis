"""Selecting devices to reboot, for the reboot action and post-deploy reboots."""

import uuid
from typing import TYPE_CHECKING, Iterable

from sqlalchemy.orm import Session
from thymis_controller import crud, models

if TYPE_CHECKING:
    from thymis_controller.network_relay import NetworkRelay


def reboot_targets(
    db_session: Session,
    network_relay: "NetworkRelay",
    deployment_info_ids: Iterable[uuid.UUID],
) -> tuple[list[models.RebootDeviceInformation], list[dict]]:
    """Split the requested devices into reachable reboot targets and skipped ones.

    Duplicates are dropped; skipped entries carry ``{"id", "reason"}`` with
    reason ``not_found`` or ``offline``.
    """
    devices: list[models.RebootDeviceInformation] = []
    skipped: list[dict] = []
    for deployment_info_id in dict.fromkeys(deployment_info_ids):
        deployment_info = crud.deployment_info.get_by_id(db_session, deployment_info_id)
        if deployment_info is None:
            skipped.append({"id": str(deployment_info_id), "reason": "not_found"})
        elif not network_relay.public_key_to_connection_id.get(
            deployment_info.ssh_public_key
        ):
            skipped.append({"id": str(deployment_info_id), "reason": "offline"})
        else:
            devices.append(
                models.RebootDeviceInformation(
                    deployment_info_id=deployment_info.id,
                    deployment_public_key=deployment_info.ssh_public_key,
                )
            )
    return devices, skipped


def should_reboot_after_deploy(
    policy: models.RebootPolicy, reboot_required: bool
) -> bool:
    """Whether a successfully deployed device is rebooted under ``policy``."""
    return policy == "always" or (policy == "if_required" and reboot_required)
