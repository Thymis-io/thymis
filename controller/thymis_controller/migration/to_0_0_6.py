def to_0_0_6(state: dict):
    state["version"] = "0.0.6"

    def modify_module_types(type_str):
        if type_str.startswith("thymis_controller.models.modules."):
            return type_str.replace(
                "thymis_controller.models.modules.", "thymis_controller.modules.", 1
            )
        return type_str

    def modify_module_settings(module_settings):
        module_settings["type"] = modify_module_types(module_settings["type"])
        for key, value in module_settings["settings"].items():
            module_settings["settings"][key] = value["value"]

    # for tags[].modules[].type and devices[].modules[].type
    for tag in state["tags"]:
        for module in tag["modules"]:
            modify_module_settings(module)
    for device in state["devices"]:
        for module in device["modules"]:
            modify_module_settings(module)

    return state
