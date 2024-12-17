import subprocess
from typing import List

from git import Tuple


def ssh_keyscan_host(host: str, port: int = 22) -> List[Tuple[str, str, str]]:
    """
    Scan the host for its ssh key

    :param host: the host to scan
    :param port: the port to scan

    :return: a list of tuples containing the host and the key
    """
    cmd = ["ssh-keyscan", "-p", str(port), host]
    result = subprocess.run(cmd, capture_output=True, check=False)

    # return empty list if the host is not reachable
    if result.returncode != 0:
        return []

    lines = result.stdout.decode("utf-8").splitlines()
    host_keys = []
    for line in lines:
        if line.startswith("#"):
            continue
        line_split = line.split(" ")
        host_keys.append((line_split[0], f"{line_split[1]} {line_split[2]}"))

    return host_keys


def determine_first_host_with_key(
    hosts: List[str], public_key: str, port: int = 22
) -> str:
    """
    Determine the first host in the list that has a key

    :param hosts: the list of hosts to check
    :param public_key: the public key to check
    :param port: the port to check

    :return: the first host that has the given key
    """

    for host in hosts:
        keys = ssh_keyscan_host(host, port)
        for key in keys:
            if key[1] == public_key:
                return host

    return None
