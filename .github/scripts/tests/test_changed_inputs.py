import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from changed_inputs import changed_inputs, risk_label  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def test_non_boot_input_is_lock_only():
    names = changed_inputs(load("base"), load("lock_only"))
    assert names == ["flake_utils"]
    assert risk_label(names) == "risk:lock-only"


def test_nixpkgs_bump_is_boot_risk():
    names = changed_inputs(load("base"), load("boot"))
    assert names == ["nixpkgs"]
    assert risk_label(names) == "risk:boot-firmware-kernel"


def test_identical_locks_have_no_changes():
    assert changed_inputs(load("base"), load("base")) == []
