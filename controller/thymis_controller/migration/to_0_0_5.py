def to_0_0_5(state: dict):
    state["version"] = "0.0.5"
    tag_name_to_identifier_map = {}

    def tag_name_to_identifier(tag):
        if tag in tag_name_to_identifier_map:
            return tag_name_to_identifier_map[tag]
        return tag

    for tag in state["tags"]:
        tag_name_to_identifier_map[tag["displayName"]] = tag["identifier"]

    for device in state["devices"]:
        device["tags"] = [tag_name_to_identifier(tag) for tag in device["tags"]]

    return state
