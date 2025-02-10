from packaging import version
from thymis_controller.migration.to_0_0_2 import to_0_0_2
from thymis_controller.migration.to_0_0_3 import to_0_0_3
from thymis_controller.migration.to_0_0_4 import to_0_0_4
from thymis_controller.migration.to_0_0_5 import to_0_0_5
from thymis_controller.migration.to_0_0_6 import to_0_0_6
from thymis_controller.migration.to_0_0_7 import to_0_0_7
from thymis_controller.migration.to_0_0_8 import to_0_0_8

KNOWN_VERSIONS = [
    "0.0.1",
    "0.0.2",
    "0.0.3",
    "0.0.4",
    "0.0.5",
    "0.0.6",
    "0.0.7",
    "0.0.8",
]  # TODO: remove this, replace with dynamic versioning


def migrate(state: dict):
    assert state["version"] in KNOWN_VERSIONS, f"Unknown version {state['version']}"

    if version.parse(state["version"]) == version.parse("0.0.1"):
        state = to_0_0_2(state)

    if version.parse(state["version"]) == version.parse("0.0.2"):
        state = to_0_0_3(state)

    if version.parse(state["version"]) == version.parse("0.0.3"):
        state = to_0_0_4(state)

    if version.parse(state["version"]) == version.parse("0.0.4"):
        state = to_0_0_5(state)

    if version.parse(state["version"]) == version.parse("0.0.5"):
        state = to_0_0_6(state)

    if version.parse(state["version"]) == version.parse("0.0.6"):
        state = to_0_0_7(state)

    if version.parse(state["version"]) == version.parse("0.0.7"):
        state = to_0_0_8(state)

    return state


latest_version = KNOWN_VERSIONS[-1]
