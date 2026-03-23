"""Background scheduler for the auto-update feature.

Reads controller settings from the DB and fires AutoUpdateTaskSubmission
at the scheduled time.  All scheduling is done in pure Python — no
dependency on systemd-analyze at runtime.

Schedule is stored as a JSON string in the auto_update_schedule column:

  {"frequency": "hourly"}
  {"frequency": "daily",            "time": "03:00"}
  {"frequency": "weekly",           "time": "03:00", "weekdays": [0, 1, 2, 3, 4]}
  {"frequency": "monthly",          "time": "03:00", "day_of_month": 1}
  {"frequency": "monthly_weekday",  "time": "03:00", "nth_weekday": 1, "weekday": 0}

weekdays / weekday: 0=Monday … 6=Sunday  (ISO weekday - 1)
nth_weekday: 1=first, 2=second, 3=third, 4=fourth, 5=fifth, -1=last
"""

import asyncio
import json
import logging
import uuid as _uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Literal

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
SCHEDULER_USER_SESSION_ID = _uuid.UUID("00000000-0000-0000-0000-000000000001")

# Default schedule: weekly Mon–Thu at 03:00 UTC
DEFAULT_SCHEDULE = {"frequency": "weekly", "time": "03:00", "weekdays": [0, 1, 2, 3]}


def parse_schedule(raw: str) -> dict:
    """Parse the schedule JSON string, falling back to the default."""
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("frequency") in (
            "hourly",
            "daily",
            "weekly",
            "monthly",
            "monthly_weekday",
        ):
            return data
    except Exception:
        pass
    logger.warning("Invalid schedule %r, using default", raw)
    return DEFAULT_SCHEDULE


def next_fire_time(schedule: dict, after: datetime) -> datetime:
    """Return the next UTC fire time for *schedule* strictly after *after*.

    *after* must be timezone-aware (UTC).
    """
    freq: Literal[
        "hourly", "daily", "weekly", "monthly", "monthly_weekday"
    ] = schedule.get("frequency", "daily")

    # Parse HH:MM — default 03:00
    time_str: str = schedule.get("time", "03:00")
    try:
        hh, mm = (int(x) for x in time_str.split(":"))
    except Exception:
        hh, mm = 3, 0

    now = after.astimezone(timezone.utc)

    if freq == "hourly":
        # Next occurrence at :mm of the next hour (or this hour if not yet reached)
        candidate = now.replace(minute=mm, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(hours=1)
        return candidate

    if freq == "daily":
        candidate = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    if freq == "weekly":
        weekdays: list[int] = schedule.get("weekdays", list(range(7)))
        if not weekdays:
            weekdays = list(range(7))
        # Try each of the next 7 days
        candidate = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        for _ in range(8):
            if candidate > now and candidate.weekday() in weekdays:
                return candidate
            candidate += timedelta(days=1)
        # Fallback: next day in weekdays
        return candidate

    if freq == "monthly":
        day: int = max(1, min(28, schedule.get("day_of_month", 1)))
        # Try this month, then next month
        for delta_months in range(2):
            month = now.month + delta_months
            year = now.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            try:
                candidate = now.replace(
                    year=year,
                    month=month,
                    day=day,
                    hour=hh,
                    minute=mm,
                    second=0,
                    microsecond=0,
                )
                if candidate > now:
                    return candidate
            except ValueError:
                pass  # day out of range for month, try next month
        # Fallback: 30 days from now
        return now + timedelta(days=30)

    if freq == "monthly_weekday":
        # nth occurrence of a weekday in a month.
        # nth_weekday: 1=first, 2=second, 3=third, 4=fourth, 5=fifth, -1=last
        # weekday: 0=Monday … 6=Sunday
        nth: int = schedule.get("nth_weekday", 1)
        target_weekday: int = schedule.get("weekday", 0)

        def nth_weekday_of_month(year: int, month: int) -> datetime | None:
            import calendar

            cal = calendar.monthcalendar(year, month)
            # collect all days matching target_weekday (col index = weekday)
            days = [week[target_weekday] for week in cal if week[target_weekday] != 0]
            if not days:
                return None
            if nth == -1:
                day = days[-1]
            else:
                idx = nth - 1
                if idx >= len(days):
                    return None
                day = days[idx]
            try:
                return now.replace(
                    year=year,
                    month=month,
                    day=day,
                    hour=hh,
                    minute=mm,
                    second=0,
                    microsecond=0,
                )
            except ValueError:
                return None

        # Try this month and the next 12 months
        for delta_months in range(13):
            month = now.month + delta_months
            year = now.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            candidate = nth_weekday_of_month(year, month)
            if candidate is not None and candidate > now:
                return candidate

        # Fallback: 30 days from now
        return now + timedelta(days=30)

    # Unknown frequency — default to 24 h
    return now + timedelta(days=1)


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
    last_schedule_raw: str | None = None

    while True:
        try:
            with sqlalchemy.orm.Session(db_engine) as db_session:
                settings = crud.controller_settings.get(db_session)
                enabled = settings.auto_update_enabled
                schedule_raw = settings.auto_update_schedule

            if not enabled:
                await asyncio.sleep(60)
                next_fire = None
                last_schedule_raw = None
                continue

            now = datetime.now(timezone.utc)
            schedule = parse_schedule(schedule_raw)

            # Recompute if schedule changed or not yet set
            if next_fire is None or schedule_raw != last_schedule_raw:
                next_fire = next_fire_time(schedule, now)
                last_schedule_raw = schedule_raw
                logger.info(
                    "Auto-update scheduled: next fire at %s (schedule=%r)",
                    next_fire.isoformat(),
                    schedule_raw,
                )

            sleep_seconds = (next_fire - now).total_seconds()

            if sleep_seconds > 1:
                # Poll at most every 30 s so schedule changes take effect quickly
                await asyncio.sleep(min(sleep_seconds, 30))
                continue

            # Time to fire
            logger.info("Firing scheduled auto-update (schedule=%r)", schedule_raw)
            next_fire = None
            last_schedule_raw = None

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
            now = datetime.now(timezone.utc)
            next_fire = next_fire_time(schedule, now)
            last_schedule_raw = schedule_raw
            logger.info("Next scheduled auto-update at %s", next_fire.isoformat())

            await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info("Auto-update scheduler stopped")
            raise
        except Exception as e:
            logger.error("Unexpected error in auto-update scheduler: %s", e)
            await asyncio.sleep(60)
