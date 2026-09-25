import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.config import global_settings
from thymis_controller.lib import read_into_base64
from thymis_controller.nix.templating import convert_python_value_to_nix
from thymis_controller.project import Project


class ThymisDevice(modules.Module):
    display_name: str = "Device"

    description = modules.LocalizedString(
        en="Core device identity: hardware type, image format, hostname and state version.",
        de="Kern-Geräteidentität: Hardwaretyp, Image-Format, Hostname und State-Version.",
    )

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice_dark.svg")
    )

    device_type = modules.Setting(
        display_name=modules.LocalizedString(
            en="Device Type",
            de="Gerätetyp",
        ),
        nix_attr_name="thymis.config.device-type",
        type=modules.SelectOneType(
            select_one=[
                ("Generic x86-64", "generic-x86_64"),
                ("Raspberry Pi 3", "raspberry-pi-3"),
                ("Raspberry Pi 4", "raspberry-pi-4"),
                ("Raspberry Pi 5", "raspberry-pi-5"),
            ],
            extra_data={
                "only_editable_on_target_type": ["config"],
            },
        ),
        default="",
        description=modules.LocalizedString(
            en="The type of device.",
            de="Der Typ des Geräts.",
        ),
        example="",
        order=10,
    )

    image_format = modules.Setting(
        display_name=modules.LocalizedString(
            en="Image Format",
            de="Image Format",
        ),
        nix_attr_name="thymis.config.image-format",
        type=modules.SelectOneType(
            select_one=[
                ("SD-Card Image", "sd-card-image"),
                ("Virtual Disk Image (qcow)", "qcow"),
                ("USB Stick Installer", "usb-stick-installer"),
                ("NixOS VM", "nixos-vm"),
            ],
            extra_data={
                "restrict_values_on_other_key": {
                    "device_type": {
                        "generic-x86_64": ["nixos-vm", "usb-stick-installer"],
                        "raspberry-pi-3": ["sd-card-image"],
                        "raspberry-pi-4": ["sd-card-image"],
                        "raspberry-pi-5": ["sd-card-image"],
                    }
                },
                "only_editable_on_target_type": ["config"],
            },
        ),
        default="",
        description=modules.LocalizedString(
            en="The image format.",
            de="Das Image-Format.",
        ),
        example="",
        order=15,
    )

    device_name = modules.Setting(
        display_name=modules.LocalizedString(
            en="Default Hostname",
            de="Standard-Hostname",
        ),
        nix_attr_name=None,  # written explicitly in write_nix_settings; skipped if empty
        type="string",
        default="",
        description=modules.LocalizedString(
            en="The hostname used for all devices in this configuration, "
            "until a device-specific name is set via the device details page. "
            "Leave blank to use the built-in default 'thymis'.",
            de="Der Hostname, der für alle Geräte dieser Konfiguration verwendet wird, "
            "bis ein gerätespezifischer Name über die Gerätedetailseite gesetzt wird. "
            "Leer lassen, um den Standard-Hostnamen 'thymis' zu verwenden.",
        ),
        example="my-raspberry-pi",
        order=20,
    )

    nix_state_version = modules.Setting(
        display_name=modules.LocalizedString(
            en="NixOS State Version",
            de="NixOS State Version",
        ),
        nix_attr_name="system.stateVersion",
        type=modules.SelectOneType(
            select_one=["24.05", "24.11", "25.05", "25.11", "26.05"]
        ),
        default="26.05",
        description=modules.LocalizedString(
            en="The NixOS state version.",
            de="Die NixOS Zustandsversion.",
        ),
        example="",
        order=25,
    )

    agent_controller_url = modules.Setting(
        display_name=modules.LocalizedString(
            en="Thymis Controller URL",
            de="Thymis Controller-URL",
        ),
        # nix_attr_name="thymis.config.agent.controller-url",
        type="string",
        default="",
        description=modules.LocalizedString(
            en="URL of this Thymis Controller instance",
            de="URL dieser Thymis Controller-Instanz",
        ),
        example="",
        order=80,
    )

    def write_nix_settings(
        self,
        f,
        path,
        module_settings: models.ModuleSettings,
        priority: int,
        project: Project,
    ):
        # get last 2 components of the path
        write_target_type = path.parts[-2]
        path.parts[-1]

        device_type = (
            module_settings.settings["device_type"]
            if "device_type" in module_settings.settings
            else self.device_type.default
        )

        image_format = (
            module_settings.settings["image_format"]
            if "image_format" in module_settings.settings
            else self.image_format.default
        )

        agent_controller_url = (
            module_settings.settings["agent_controller_url"]
            if "agent_controller_url" in module_settings.settings
            else self.agent_controller_url.default
        )

        f.write("  imports = [\n")

        if write_target_type == "hosts":
            if device_type:
                f.write(f"    inputs.thymis.nixosModules.thymis-device-{device_type}\n")
            if image_format:
                f.write(f"    inputs.thymis.nixosModules.thymis-image-{image_format}\n")
            elif device_type:
                first_format = self.find_image_format_by_device_type(device_type)
                f.write(f"    inputs.thymis.nixosModules.thymis-image-{first_format}\n")

        f.write("  ];\n")

        if agent_controller_url:
            f.write(
                f"  thymis.config.agent.controller-url = lib.mkOverride {priority} {convert_python_value_to_nix(agent_controller_url)};\n"
            )
        else:
            default_agent_controller_url = (
                global_settings.AGENT_ACCESS_URL or global_settings.BASE_URL or ""
            )
            f.write(
                f"  thymis.config.agent.controller-url = lib.mkOverride 100 {convert_python_value_to_nix(default_agent_controller_url)};\n"
            )

        # omit device-name when blank so the Nix module default ("thymis") applies
        device_name_value = module_settings.settings.get("device_name", "") or ""
        if device_name_value:
            f.write(
                f"  thymis.config.device-name = lib.mkOverride {priority} "
                f"{convert_python_value_to_nix(device_name_value)};\n"
            )

        return super().write_nix_settings(f, path, module_settings, priority, project)

    def find_image_format_by_device_type(self, device_type):
        restricted = self.image_format.type.extra_data["restrict_values_on_other_key"]
        available_formats = restricted["device_type"][device_type]

        return next(
            (
                format[1]
                for format in self.image_format.type.select_one
                if format[1] in available_formats
            ),
            None,
        )
