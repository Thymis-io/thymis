from thymis_controller import models, modules
from thymis_controller.models import ModuleSettings


class ThymisController(modules.Module):
    displayName: str = "Thymis Controller"

    repo_dir = models.Setting(
        name="thymis.controller.repo-dir",
        type="string",
        default="/var/lib/thymis",
        description="The directory where the thymis repository is located.",
        example="/var/lib/thymis",
    )

    def write_nix_settings(self, f, module_settings: ModuleSettings, priority: int):
        f.write("  thymis.controller.enable = true;\n")

        return super().write_nix_settings(f, module_settings, priority)


class ThymisDevice(modules.Module):
    displayName: str = "Thymis Device"

    device_type = models.Setting(
        name="thymis.config.device-type",
        type="select-one",
        options=[dt.value for dt in models.DeviceType],
        default="",
        description="The device type of the thymis device.",
        example="",
        order=10,
    )

    device_name = models.Setting(
        name="thymis.config.device-name",
        type="string",
        default="",
        description="The device name of the thymis device.",
        example="",
        order=20,
    )

    password = models.Setting(
        name="thymis.config.password",
        type="string",
        default="",
        description="The password of the thymis device.",
        example="",
        order=30,
    )

    wifi_ssid = models.Setting(
        name="thymis.config.wifi-ssid",
        type="string",
        default="",
        description="The wifi ssid of the thymis device.",
        example="",
        order=40,
    )

    wifi_password = models.Setting(
        name="thymis.config.wifi-password",
        type="string",
        default="",
        description="The wifi password of the thymis device.",
        example="",
        order=50,
    )

    image_format = models.Setting(
        name="thymis.config.image-format",
        type="select-one",
        options=[if_.value for if_ in models.ImageFormat],
        default=models.ImageFormat.img.value,
        description="The image format of the thymis device.",
        example="",
        order=60,
    )

    def write_nix_settings(self, f, module_settings: ModuleSettings, priority: int):
        device_type = (
            module_settings.settings["device_type"]
            if "device_type" in module_settings.settings
            else self.device_type.default
        )

        if device_type:
            f.write(f"  imports = [\n")
            f.write(f"    inputs.thymis.nixosModules.thymis-device-{device_type}\n")
            f.write(f"  ];\n")

        return super().write_nix_settings(f, module_settings, priority)
