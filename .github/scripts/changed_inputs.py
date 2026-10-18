"""Print the root inputs whose locked revision differs between two flake.lock files.

Usage: changed_inputs.py OLD NEW          -> changed input names, space separated
       changed_inputs.py OLD NEW --label  -> risk label for the PR
"""
import json
import re
import sys

BOOT_RISK = re.compile(r"nixpkgs|nixos-raspberrypi|raspberry-pi-nix|nixos-hardware|home-manager")
LABEL_LOCK_ONLY = "risk:lock-only"
LABEL_BOOT = "risk:boot-firmware-kernel"


def locked_by_input(lock):
    nodes = lock["nodes"]
    result = {}
    for name, node_key in nodes["root"].get("inputs", {}).items():
        if isinstance(node_key, list):  # "follows" path, not locked itself
            continue
        locked = nodes[node_key].get("locked", {})
        result[name] = locked.get("rev") or locked.get("narHash")
    return result


def changed_inputs(old_lock, new_lock):
    old, new = locked_by_input(old_lock), locked_by_input(new_lock)
    return sorted(name for name in old.keys() | new.keys() if old.get(name) != new.get(name))


def risk_label(names):
    return LABEL_BOOT if any(BOOT_RISK.search(n) for n in names) else LABEL_LOCK_ONLY


def main(argv):
    with open(argv[1]) as f:
        old = json.load(f)
    with open(argv[2]) as f:
        new = json.load(f)
    names = changed_inputs(old, new)
    print(risk_label(names) if "--label" in argv[3:] else " ".join(names))


if __name__ == "__main__":
    main(sys.argv)
