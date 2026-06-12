"""Split the monolithic ThymisDevice ("Core Device Configuration") module into
separate modules. Settings that moved out of ThymisDevice are relocated into the
new module they now belong to. device_type, image_format, device_name,
nix_state_version and agent_controller_url stay in ThymisDevice (the Device module).
"""

THYMIS_DEVICE = "thymis_controller.modules.thymis.ThymisDevice"
NETWORKING = "thymis_controller.modules.networking.NetworkingModule"
LOCALIZATION = "thymis_controller.modules.localization.LocalizationModule"
SECURITY = "thymis_controller.modules.security.SecurityAccessModule"
FILES = "thymis_controller.modules.files.FilesModule"

# setting key on the old ThymisDevice module -> module type it moves to
KEY_TO_MODULE = {
    "wifi_ssid": NETWORKING,
    "wifi_password": NETWORKING,
    "wifi_auth": NETWORKING,
    "wifi_auth_protocols": NETWORKING,
    "static_networks": NETWORKING,
    "nameservers": NETWORKING,
    "timezone": LOCALIZATION,
    "time_servers": LOCALIZATION,
    "password_secret": SECURITY,
    "authorized_keys": SECURITY,
    "security_pki_certificates": SECURITY,
    "secrets": FILES,
    "artifacts": FILES,
}


def _migrate_modules(module_list: list):
    # map of already-present module settings objects by type, to merge into
    existing = {}
    for module in module_list:
        existing.setdefault(module.get("type"), module)

    # settings for modules that need to be created, keyed by target type
    new_modules: dict[str, dict] = {}

    for module in module_list:
        if module.get("type") != THYMIS_DEVICE:
            continue
        settings = module.get("settings", {})
        for key in list(settings.keys()):
            target_type = KEY_TO_MODULE.get(key)
            if target_type is None:
                continue
            value = settings.pop(key)
            if target_type in existing:
                existing[target_type].setdefault("settings", {})[key] = value
            else:
                new_modules.setdefault(target_type, {})[key] = value

    for target_type, settings in new_modules.items():
        module_list.append({"type": target_type, "settings": settings})


def to_0_0_9(state: dict):
    state["version"] = "0.0.9"
    for config in state.get("configs", []):
        _migrate_modules(config.get("modules", []))
    for tag in state.get("tags", []):
        _migrate_modules(tag.get("modules", []))
    return state
