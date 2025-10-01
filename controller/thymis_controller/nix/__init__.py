import json
import logging
import os
import pathlib
import re
import subprocess
from typing import TYPE_CHECKING

from thymis_controller.models.external_repo import (
    FlakeReference,
    GitFlakeReference,
    GithubFlakeReference,
)
from thymis_controller.nix.flake_reference import parse_flake_reference

from .log_parse import NixParser

if TYPE_CHECKING:
    from thymis_controller.models.secrets import SecretShort

logger = logging.getLogger(__name__)


def get_input_out_path(flake_path, input_name):
    # first run `nix build .#inputs.<input_name>.outPath`
    # then run `nix eval .#inputs.<input_name>.outPath --json`
    cmd = NIX_CMD + [
        "build",
        f"{flake_path}#inputs.{input_name}.outPath",
        "--no-link",
        "--allow-dirty-locks",
        "--refresh",
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            cwd=flake_path,
            stderr=subprocess.PIPE,
            env={
                "PATH": os.getenv("PATH"),
                "NIX_SSHOPTS": NIX_SSHOPTS,
                "GIT_TERMINAL_PROMPT": "0",
            },
        )
    except subprocess.CalledProcessError as e:
        nix_parser = NixParser()
        nix_parser.process_buffer(bytearray(e.stderr))
        logger.error(
            "Command failed: %s with exit code %s: %s",
            e.cmd,
            e.returncode,
            nix_parser.msg_output,
        )
        return None, nix_parser.msg_output

    cmd = NIX_CMD + [
        "eval",
        f"{flake_path}#inputs.{input_name}.outPath",
        "--json",
        "--allow-dirty-locks",
        "--refresh",
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            cwd=flake_path,
            env={
                "PATH": os.getenv("PATH"),
                "NIX_SSHOPTS": NIX_SSHOPTS,
                "GIT_TERMINAL_PROMPT": "0",
            },
        )
    except subprocess.CalledProcessError as e:
        nix_parser = NixParser()
        nix_parser.process_buffer(bytearray(e.stderr))
        logger.error(
            "Command failed: %s with exit code %s: %s",
            e.cmd,
            e.returncode,
            nix_parser.msg_output,
        )
        return None, nix_parser.msg_output

    # result.stdout is a json string
    result = json.loads(result.stdout)
    # should be a string
    assert isinstance(result, str)
    return result, None


def get_build_output(flake_path, identifier):
    cmd = NIX_CMD + [
        "build",
        f"{flake_path}#nixosConfigurations.{identifier}.config.system.build.toplevel",
        "--json",
        "--allow-dirty-locks",
    ]

    try:
        result = subprocess.run(cmd, check=True, cwd=flake_path, capture_output=True)
    except subprocess.CalledProcessError as e:
        nix_parser = NixParser()
        nix_parser.process_buffer(bytearray(e.stderr))
        logger.error(
            "Command failed: %s with exit code %s: %s",
            e.cmd,
            e.returncode,
            nix_parser.msg_output,
        )
        return None

    result = json.loads(result.stdout)
    # should be a dict
    assert isinstance(result, list)
    return result[0]


def check_device_reference(
    flake_path: pathlib.Path, commit_hash: str, config_id: str
) -> bool:
    """
    Check if a device can be mapped to the Nix repository
    :param flake_path: path to the flake
    :param commit_hash: commit hash
    :param config_id: configuration id
    :return: True if the device can be mapped to the Nix repository, False otherwise
    """

    def check_is_commit_hash(s):
        return re.match(r"^[0-9a-f]{40}$", s) is not None

    if not check_is_commit_hash(commit_hash):
        return False

    def check_is_config_id(s):
        # just don't make it too long, we don't want to have a DoS attack
        return len(s) < 1024

    if not check_is_config_id(config_id):
        return False

    git_check_commit_exists_cmd = ["git", "cat-file", "-e", commit_hash + "^{commit}"]
    try:
        subprocess.run(
            git_check_commit_exists_cmd,
            check=True,
            cwd=flake_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        logger.error(
            "Check device reference failed: Commit hash %s does not exist: %s",
            commit_hash,
            e.stderr.decode(),
        )
        return False

    cmd = NIX_CMD + [
        "eval",
        f"{flake_path}?rev={commit_hash}#nixosConfigurations",
        "--apply",
        "builtins.attrNames",
        "--json",
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            cwd=flake_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        logger.error(
            "Check device reference failed: %s with exit code %s: %s\n%s",
            e.cmd,
            e.returncode,
            e.stdout.decode(),
            e.stderr.decode(),
        )

    try:
        result = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        logger.error("Check device reference failed: Could not decode JSON: %s", e)
        return False

    if not isinstance(result, list):
        logger.error(
            "Check device reference failed: Expected a list, got %s", type(result)
        )
        return False

    return config_id in result


def get_nix_access_tokens(flake_url: str, api_key: "SecretShort | None") -> str:
    flake_ref = parse_flake_reference(flake_url)
    if flake_ref and api_key:
        if isinstance(flake_ref, GitFlakeReference):
            return f"access-tokens = {flake_ref.host}={api_key.value_str}"
        elif isinstance(flake_ref, GithubFlakeReference):
            return f"access-tokens = github.com={api_key.value_str}"
    return ""


def nix_flake_prefetch(url: str, api_key: "SecretShort | None"):
    access_token = get_nix_access_tokens(url, api_key)

    try:
        subprocess.run(
            [
                "nix",
                *NIX_CMD[1:],
                "flake",
                "prefetch",
                url,
                "--refresh",
                "--tarball-ttl",
                "0",
            ],
            capture_output=True,
            check=True,
            env={
                "PATH": os.getenv("PATH"),
                "NIX_SSHOPTS": NIX_SSHOPTS,
                "GIT_TERMINAL_PROMPT": "0",
                "NIX_CONFIG": (access_token),
            },
        )
    except subprocess.CalledProcessError as e:
        nix_parser = NixParser()
        nix_parser.process_buffer(bytearray(e.stderr))
        return False, nix_parser.msg_output
    return True, None


NIX_CMD = [
    "nix",
    "--option",
    "extra-experimental-features",
    "nix-command flakes",
    "--option",
    "extra-substituters",
    "https://cache.thymis.io",
    "--option",
    "extra-trusted-public-keys",
    "cache.thymis.io-1:pEeKkNXiK17TLKls0KM8cEp0NGy08gc5chAmCyuQo8M=",
    "--log-format",
    "internal-json",
]

NIX_SSHOPTS = (
    "-o PasswordAuthentication=no "
    "-o KbdInteractiveAuthentication=no "
    "-o BatchMode=yes "
    "-o NumberOfPasswordPrompts=0"
    "-o ConnectTimeout=10 "
)
