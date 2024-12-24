import json
import logging
import pathlib
import re
import subprocess
import typing

import jinja2
from pydantic import BaseModel, Discriminator, Tag, ValidationError

logger = logging.getLogger(__name__)


def string_can_be_identifier_for_attrs_key(s):
    # see https://nix.dev/manual/nix/2.18/language/values#attribute-set
    # name = identifier | string
    # identifier ~ [a-zA-Z_][a-zA-Z0-9_'-]*
    if not s:
        return False
    if not s[0].isalpha() and s[0] != "_":
        return False
    for c in s:
        if not c.isalnum() and c not in "_'-":
            return False
    return True


def write_comma_separated_identifier_list(identifiers):
    for identifier in identifiers:
        assert string_can_be_identifier_for_attrs_key(
            identifier
        ), f"Invalid identifier: {identifier}"
    if identifiers:
        identifiers = [""] + identifiers
    return "\n,".join(identifiers)


def convert_python_value_to_nix(value, ident=0):
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        # see https://nix.dev/manual/nix/2.18/language/values#type-string
        value = value.replace("\\", "\\\\")
        value = value.replace('"', '\\"')
        value = value.replace("${", "\\${")
        value = value.replace("\n", "\\n")
        value = value.replace("\t", "\\t")
        value = value.replace("\r", "\\r")
        return f'"{value}"'
    elif isinstance(value, list):
        list_line = "\n" + "  " * (ident + 1)
        return (
            f"[{list_line}"
            f"{list_line.join([convert_python_value_to_nix(v) for v in value if v is not None])}\n"
            f"{'  ' * ident}]"
        )
    elif isinstance(value, dict):
        # we like the form { key1.key2.key....keyN = value; }
        if len(value) == 0:
            return "{}"
        queue = [[k] for k in value.keys()]
        result = {}

        def get_subvalue(value, key_list):
            for key in key_list:
                value = value[key]
            return value

        while queue:
            key_list = queue.pop(0)
            subvalue = get_subvalue(value, key_list)
            if isinstance(subvalue, dict):
                for k in subvalue.keys():
                    queue.append(key_list + [k])
            else:
                key_list = [
                    (
                        k
                        if string_can_be_identifier_for_attrs_key(k)
                        else convert_python_value_to_nix(k)
                    )
                    for k in key_list
                ]
                result[".".join(key_list)] = subvalue
        return (
            "{\n"
            + "\n".join(
                [
                    f"  {k} = {convert_python_value_to_nix(v)};"
                    for k, v in result.items()
                ]
            )
            + "\n}"
        )
    else:
        return str(value)


def format_nix_file(file_path):
    cmd = ["nixpkgs-fmt", file_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(
            "Command failed: %s with exit code %s: %s",
            e.cmd,
            e.returncode,
            e.stderr.decode(),
        )


def format_nix_value_as_string(value: str):
    cmd = ["nixpkgs-fmt"]
    result = subprocess.run(
        cmd, shell=True, check=True, capture_output=True, input=value.encode()
    )
    return result.stdout.decode()


def get_input_out_path(flake_path, input_name):
    # first run `nix build .#inputs.<input_name>.outPath`
    # then run `nix eval .#inputs.<input_name>.outPath --json`
    cmd = NIX_CMD + ["build", f"{flake_path}#inputs.{input_name}.outPath", "--no-link"]

    try:
        subprocess.run(cmd, check=True, cwd=flake_path, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        logger.error(
            "Command failed: %s with exit code %s: %s",
            e.cmd,
            e.returncode,
            e.stderr.decode(),
        )
        return None

    cmd = NIX_CMD + ["eval", f"{flake_path}#inputs.{input_name}.outPath", "--json"]
    result = subprocess.run(cmd, check=True, capture_output=True, cwd=flake_path)
    # result.stdout is a json string
    result = json.loads(result.stdout)
    # should be a string
    assert isinstance(result, str)
    return result


template_env = jinja2.Environment(
    loader=jinja2.PackageLoader("thymis_controller", "templates_nix"),
    block_start_string='"{%',
    variable_start_string='"{{',
    block_end_string='%}"',
    variable_end_string='}}"',
)

template_env.globals[
    "string_can_be_identifier_for_attrs_key"
] = string_can_be_identifier_for_attrs_key
template_env.globals[
    "write_comma_separated_identifier_list"
] = write_comma_separated_identifier_list
template_env.globals["convert_python_value_to_nix"] = convert_python_value_to_nix

# the following blocks of code may go somewhere else in the future
if typing.TYPE_CHECKING:
    from thymis_controller import models


def render_flake_nix(repositories: dict[str, "models.Repo"]) -> str:
    template = template_env.get_template("flake.nix.j2")
    inputs = {}
    for name, repo in repositories.items():
        inputs[name] = {}
        if repo.url:
            inputs[name]["url"] = repo.url
        if repo.follows:
            inputs[name]["follows"] = repo.follows
        for key, value in repo.inputs_follows.items():
            inputs[name]["inputs"] = {}
            inputs[name]["inputs"][key] = {}
            inputs[name]["inputs"][key]["follows"] = value
    from thymis_controller import project

    inputs_keys = [k for k in inputs.keys() if k not in project.BUILTIN_REPOSITORIES]
    rendered = template.render(inputs=inputs, inputs_keys=inputs_keys)
    formatted = format_nix_value_as_string(rendered)
    return formatted


def get_build_output(flake_path, identifier):
    cmd = NIX_CMD + [
        "build",
        f"{flake_path}#nixosConfigurations.{identifier}.config.system.build.toplevel",
        "--json",
    ]

    try:
        result = subprocess.run(cmd, check=True, cwd=flake_path, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(
            "Command failed: %s with exit code %s: %s",
            e.cmd,
            e.returncode,
            e.stderr.decode(),
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
        return re.match(r"[0-9a-f]{40}", s) is not None

    if not check_is_commit_hash(commit_hash):
        return False

    def check_is_config_id(s):
        # just don't make it too long, we don't want to have a DoS attack
        return len(s) < 1024

    if not check_is_config_id(config_id):
        return False

    git_check_commit_exists_cmd = ["git", "cat-file", "-e", f"{commit_hash}^{{commit}}"]
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
]
