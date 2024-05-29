def to_0_0_4(state: dict):
    state["version"] = "0.0.4"

    for repo in state["repositories"]:
        state["repositories"][repo]["inputs_follows"] = {}

    return state
