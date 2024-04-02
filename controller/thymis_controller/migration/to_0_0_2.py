def to_0_0_2(state: dict):
    state["tags"] = state.get("tags", [])
    state["devices"] = state.get("devices", [])

    for tag in state["tags"]:
        tag["displayName"] = tag.pop("name")
        tag["identifier"] = tag["displayName"].lower().replace(" ", "-")

    for device in state["devices"]:
        device["identifier"] = device["displayName"].lower().replace(" ", "-")
        device["targetHost"] = device.pop("hostname")

    state["version"] = "0.0.2"

    def replace_app_dot_with_thymis_controller(type_str):
        if type_str.startswith("app."):
            return type_str.replace("app.", "thymis_controller.", 1)
        return type_str

    # for tags[].modules[].type and devices[].modules[].type
    for tag in state["tags"]:
        for module in tag["modules"]:
            module["type"] = replace_app_dot_with_thymis_controller(module["type"])
    for device in state["devices"]:
        for module in device["modules"]:
            module["type"] = replace_app_dot_with_thymis_controller(module["type"])

    return state
