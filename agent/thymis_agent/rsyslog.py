"""Forwarding the device's syslog to the controller via rsyslog's omhttp."""

import asyncio
import os
import subprocess

from thymis_agent import logger
from thymis_agent.host_keys import detect_public_key
from thymis_agent.system_info import detect_hostname

RSYSLOG_CONFIG_DIR = "/etc/rsyslog.d"
RSYSLOG_CONFIG_PATH = f"{RSYSLOG_CONFIG_DIR}/thymis.conf"


def parse_controller_host(controller_host: str) -> tuple[str, str, str, str]:
    """Split the controller URL into omhttp settings.

    Returns ``(server, serverport, restpath, useHttps)``.
    """
    is_https = controller_host.startswith("https")
    authority, _, path = controller_host.split("://")[1].partition("/")
    server = authority.split(":")[0]
    if ":" in authority:
        port = authority.split(":")[1]
    else:
        port = "443" if is_https else "80"
    restpath = f"{path}/agent/logs".lstrip("/")
    return server, port, restpath, "on" if is_https else "off"


def render_rsyslog_config(
    controller_host: str, token: str, public_key: str, hostname: str
) -> str:
    server, port, restpath, use_https = parse_controller_host(controller_host)
    return f"""
            module(load="imuxsock")
            module(load="imklog")
            module(load="omhttp")
            template(name="tpl_omhttp_json" type="list") {{
                constant(value="{{")   property(name="msg"           outname="message"   format="jsonfr")
                constant(value=",")   property(name="syslogfacility" outname="facility" format="jsonfr" datatype="number")
                constant(value=",")   property(name="syslogseverity" outname="severity" format="jsonfr" datatype="number")
                constant(value=",")   property(name="syslogtag"     outname="syslogtag" format="jsonfr")
                constant(value=",")   property(name="programname"   outname="programname" format="jsonfr")
                constant(value=",")   property(name="hostname"      outname="host"      format="jsonfr")
                constant(value=",")   property(name="timereported"  outname="timestamp" format="jsonfr" dateFormat="rfc3339" date.inUTC="on")
                constant(value=",")   property(name="uuid"         outname="uuid"      format="jsonfr")
                constant(value="}}")
            }}
            template(name="tpl_echo" type="string" string="%msg%")
            ruleset(name="rs_retry_forever") {{
                action(
                    type="omhttp"
                    template="tpl_omhttp_json"
                    httpheaders=[
                        "X-Thymis-Ssh-Pubkey: {public_key}",
                        "X-Thymis-Token: {token}",
                        "X-Thymis-Hostname: {hostname}"
                    ]
                    server="{server}"
                    serverport="{port}"
                    restpath="{restpath}"
                    useHttps="{use_https}"
                    batch="on"
                    batch.format="jsonarray"
                    retry="on"
                    retry.ruleset="rs_omhttp_retry"
                    restpathtimeout="5000"
                )
            }}
            ruleset(name="rs_omhttp_retry") {{
                action(
                    type="omhttp"
                    template="tpl_echo"
                    httpheaders=[
                        "X-Thymis-Ssh-Pubkey: {public_key}",
                        "X-Thymis-Token: {token}",
                        "X-Thymis-Hostname: {hostname}"
                    ]
                    server="{server}"
                    serverport="{port}"
                    restpath="{restpath}"
                    useHttps="{use_https}"
                    batch="on"
                    batch.format="jsonarray"
                    batch.maxsize="1"
                    action.resumeRetryCount="3"
                    action.resumeInterval="20"
                    errorfile="/var/log/rsyslog-error.log"
                    restpathtimeout="5000"
                )
            }}

            call rs_retry_forever
            """


def write_rsyslog_config(controller_host: str, token: str) -> bool:
    """Write the rsyslog config. Returns True if the file changed."""
    if not token:
        return False

    rsyslog_config = render_rsyslog_config(
        controller_host, token, detect_public_key(), detect_hostname()
    )

    os.makedirs(RSYSLOG_CONFIG_DIR, exist_ok=True, mode=0o755)
    if os.path.exists(RSYSLOG_CONFIG_PATH):
        with open(RSYSLOG_CONFIG_PATH, "r", encoding="utf-8") as f:
            existing_config = f.read()
    else:
        existing_config = None
    if existing_config == rsyslog_config:
        return False
    with open(RSYSLOG_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(rsyslog_config)
    return True


def schedule_rsyslog_reload_on_activation() -> None:
    """Let NixOS activation reload syslog, for when running inside it."""
    os.makedirs("/run/nixos", exist_ok=True, mode=0o755)
    with open("/run/nixos/activation-reload-list", "a+", encoding="utf-8") as f:
        f.write("syslog.service\n")


def reload_rsyslog_sync() -> None:
    subprocess.run(["systemctl", "reload", "syslog.service"], check=False)


async def reload_rsyslog() -> None:
    proc = await asyncio.create_subprocess_exec(
        "systemctl",
        "reload",
        "syslog.service",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error(
            "Failed to reload syslog.service: %s",
            stderr.decode(),
        )
    else:
        logger.info("syslog.service reloaded successfully")
