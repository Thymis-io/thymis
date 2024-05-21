import subprocess
import json


def convert_python_value_to_nix(value):
    if isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, list):
        return f"[{' '.join([convert_python_value_to_nix(v) for v in value])}]"
    else:
        return str(value)


def get_input_out_path(flake_path, input_name):
    # first run `nix build .#inputs.<input_name>.outPath`
    # then run `nix eval .#inputs.<input_name>.outPath --json`
    cmd = f"nix build {flake_path}#inputs.{input_name}.outPath"
    subprocess.run(cmd, shell=True, check=True, cwd=flake_path)
    cmd = f"nix eval {flake_path}#inputs.{input_name}.outPath --json"
    result = subprocess.run(
        cmd, shell=True, check=True, capture_output=True, cwd=flake_path
    )
    # result.stdout is a json string
    result = json.loads(result.stdout)
    # should be a string
    assert isinstance(result, str)
    return result
