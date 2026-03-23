"""Background scheduler for the auto-update feature.

Reads controller settings from the DB, parses the systemd OnCalendar
expression using ``systemd-analyze calendar``, and submits an
``AutoUpdateTaskSubmission`` at the scheduled time.
"""

import asyncio
import logging
import subprocess
import uuid
import uuid as _uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import sqlalchemy.orm
from thymis_agent import agent
from thymis_controller import crud, models
from thymis_controller.config import global_settings

if TYPE_CHECKING:
    from thymis_controller.network_relay import NetworkRelay
    from thymis_controller.project import Project
    from thymis_controller.task.controller import TaskController

logger = logging.getLogger(__name__)

# Sentinel user session id used for scheduler-originated tasks
SCHEDULER_USER_SESSION_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _next_elapse_from_schedule(schedule: str) -> datetime | None:
    """Return the next UTC elapse time for a systemd OnCalendar expression.

    Returns ``None`` if ``systemd-analyze`` is unavailable or the expression
    is invalid.
    """
    try:
        result = subprocess.run(
            ["systemd-analyze", "calendar", "--iterations=1", schedule],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            logger.warning(
                "systemd-analyze calendar failed for %r: %s", schedule, result.stderr
            )
            return None
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("Next elapse:"):
                # Format: "Next elapse: Mon 2026-03-23 03:00:00 UTC"
                # or with a local timezone like "Wed 2026-03-25 03:00:00 CET"
                # We try to parse the datetime portion.
                raw = line.removeprefix("Next elapse:").strip()
                # raw is like "Mon 2026-03-23 03:00:00 UTC"
                # Also handle "(in …)" suffix:
                raw = raw.split(" (")[0].strip()
                # Drop the weekday prefix (first token)
                parts = raw.split()
                if len(parts) >= 3:
                    dt_str = " ".join(parts[1:])  # e.g. "2026-03-23 03:00:00 UTC"
                    # Try with timezone abbreviation
                    try:
                        from datetime import datetime as _dt

                        import dateutil.parser  # type: ignore[import]

                        return dateutil.parser.parse(dt_str).astimezone(timezone.utc)
                    except Exception:
                        pass
                    # Fallback: strip tz token, treat as UTC
                    try:
                        from datetime import datetime as _dt

                        dt_no_tz = " ".join(parts[1:3])
                        return _dt.strptime(dt_no_tz, "%Y-%m-%d %H:%M:%S").replace(
                            tzinfo=timezone.utc
                        )
                    except Exception:
                        pass
        logger.warning("Could not parse next elapse from systemd-analyze output")
        return None
    except FileNotFoundError:
        logger.warning("systemd-analyze not found; auto-update scheduler disabled")
        return None
    except Exception as e:
        logger.warning("Error calling systemd-analyze: %s", e)
        return None


def _collect_devices(
    project: "Project",
    network_relay: "NetworkRelay",
    db_session: sqlalchemy.orm.Session,
) -> list[models.DeployDeviceInformation]:
    devices: list[models.DeployDeviceInformation] = []
    for deployment_info in crud.deployment_info.get_all(db_session):
        if not network_relay.public_key_to_connection_id.get(
            deployment_info.ssh_public_key
        ):
            continue
        state = project.read_state()
        config = next(
            (
                c
                for c in state.configs
                if c.identifier == deployment_info.deployed_config_id
            ),
            None,
        )
        if config is None:
            continue
        modules = project.get_modules_for_config(state, config)
        secrets = []
        for module, settings in modules:
            for secret_type, secret in module.register_secret_settings(
                settings, project
            ):
                project.get_secret(db_session, _uuid.UUID(secret))
                secrets.append(
                    agent.SecretForDevice(
                        secret_id=secret,
                        path=secret_type.on_device_path,
                        owner=secret_type.on_device_owner,
                        group=secret_type.on_device_group,
                        mode=secret_type.on_device_mode,
                    )
                )
        devices.append(
            models.DeployDeviceInformation(
                identifier=deployment_info.deployed_config_id,
                deployment_info_id=deployment_info.id,
                deployment_public_key=deployment_info.ssh_public_key,
                secrets=secrets,
            )
        )
    return devices


async def auto_update_scheduler_loop(
    db_engine: sqlalchemy.Engine,
    project: "Project",
    task_controller: "TaskController",
    network_relay: "NetworkRelay",
):
    """Async loop that fires auto-update tasks according to the configured schedule."""
    logger.info("Auto-update scheduler started")
    next_fire: datetime | None = None

    while True:
        try:
            with sqlalchemy.orm.Session(db_engine) as db_session:
                settings = crud.controller_settings.get(db_session)
                enabled = settings.auto_update_enabled
                schedule = settings.auto_update_schedule

            if not enabled:
                # Disabled — check again in 60 s
                await asyncio.sleep(60)
                next_fire = None
                continue

            now = datetime.now(timezone.utc)

            # (Re-)compute next fire time if we don't have one yet
            if next_fire is None:
                next_fire = _next_elapse_from_schedule(schedule)
                if next_fire is None:
                    logger.warning(
                        "Could not determine next elapse for schedule %r; "
                        "retrying in 60 s",
                        schedule,
                    )
                    await asyncio.sleep(60)
                    continue
                logger.info(
                    "Auto-update scheduled: next fire at %s (schedule=%r)",
                    next_fire.isoformat(),
                    schedule,
                )

            sleep_seconds = (next_fire - now).total_seconds()

            if sleep_seconds > 1:
                # Poll at most every 30 s so schedule changes take effect quickly
                await asyncio.sleep(min(sleep_seconds, 30))
                continue

            # It's time — fire the auto-update
            logger.info("Firing scheduled auto-update (schedule=%r)", schedule)
            next_fire = None  # will be recomputed after submission

            try:
                with sqlalchemy.orm.Session(db_engine) as db_session:
                    project.update_known_hosts(db_session)
                    devices = _collect_devices(project, network_relay, db_session)
                    access_tokens = project.nix_access_tokens()

                    task_controller.submit(
                        models.AutoUpdateTaskSubmission(
                            project_path=str(project.path),
                            nix_access_tokens=access_tokens,
                            devices=devices,
                            ssh_key_path=str(
                                global_settings.PROJECT_PATH / "id_thymis"
                            ),
                            known_hosts_path=str(project.known_hosts_path),
                            controller_ssh_pubkey=project.public_key,
                        ),
                        user_session_id=SCHEDULER_USER_SESSION_ID,
                        db_session=db_session,
                    )
                logger.info("Scheduled auto-update task submitted successfully")
            except Exception as e:
                logger.error("Failed to submit scheduled auto-update task: %s", e)

            # Compute next fire time after submission
            next_fire = _next_elapse_from_schedule(schedule)
            if next_fire:
                logger.info("Next scheduled auto-update at %s", next_fire.isoformat())

            # Small sleep to avoid tight-looping if next_fire couldn't be computed
            await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info("Auto-update scheduler stopped")
            raise
        except Exception as e:
            logger.error("Unexpected error in auto-update scheduler: %s", e)
            await asyncio.sleep(60)
