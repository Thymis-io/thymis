def to_0_0_7(state: dict):
    state["version"] = "0.0.7"

    def remove_taget_host(device_settings):
        if "targetHost" in device_settings:
            print(
                f"Removing targetHost {device_settings['targetHost']} from device {device_settings['displayName']} ({device_settings['identifier']})"
            )
            del device_settings["targetHost"]

    for device in state["devices"]:
        remove_taget_host(device)

    return state
