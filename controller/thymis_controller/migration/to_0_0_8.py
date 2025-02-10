def to_0_0_8(state: dict):
    state["version"] = "0.0.8"
    state["configs"] = state.pop("devices")
    return state
