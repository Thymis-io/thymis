from thymis_controller import models, modules
from thymis_controller.models import ModuleSettings
from thymis_controller.nix import convert_python_value_to_nix


class ThymisController(modules.Module):
    displayName: str = "Thymis Controller"

    # repo_dir = models.Setting(
    #     name="thymis.controller.repo-dir",
    #     type="string",
    #     default="/var/lib/thymis",
    #     description="The directory where the thymis repository is located.",
    #     example="/var/lib/thymis",
    # )
    repo_dir = models.Setting(
        name="services.thymis-controller.repo-path",
        type="string",
        default=None,
        description="Directory where the controller will store the repository holding the project",
        example="/var/lib/thymis/repository",
        order=10,
    )
    database_url = models.Setting(
        name="services.thymis-controller.database-url",
        type="string",
        default=None,
        description="URL of the database",
        example="sqlite:////var/lib/thymis/thymis.sqlite",
        order=20,
    )
    base_url = models.Setting(
        name="services.thymis-controller.base-url",
        type="string",
        default=None,
        description="Base URL of the controller, how it will be accessed from the outside",
        example="http://localhost:8000",
        order=30,
    )
    auth_basic = models.Setting(
        name="services.thymis-controller.auth-basic",
        type="bool",
        default=None,
        description="Whether to enable authentication using a basic username/password",
        example="true",
        order=40,
    )
    auth_basic_username = models.Setting(
        name="services.thymis-controller.auth-basic-username",
        type="string",
        default=None,
        description="Username for basic authentication",
        example="admin",
        order=50,
    )
    auth_basic_password_file = models.Setting(
        name="services.thymis-controller.auth-basic-password-file",
        type="path",
        default=None,
        description="File containing the password for basic authentication",
        example="/var/lib/thymis/auth-basic-password",
        order=60,
    )
    listen_host = models.Setting(
        name="services.thymis-controller.listen-host",
        type="string",
        default=None,
        description="Host on which the controller listens for incoming connections",
        example="127.0.0.1",
        order=70,
    )
    listen_port = models.Setting(
        name="services.thymis-controller.listen-port",
        type="int",
        default=None,
        description="Port on which the controller listens for incoming connections",
        example="8000",
        order=80,
    )
    nginx_vhost_enable = models.Setting(
        name="services.thymis-controller.nginx-vhost-enable",
        type="bool",
        default=None,
        description="Whether to enable the Nginx virtual host",
        example="true",
        order=90,
    )
    nginx_vhost_name = models.Setting(
        name="services.thymis-controller.nginx-vhost-name",
        type="string",
        default=None,
        description="Name of the Nginx virtual host",
        example="thymis",
        order=100,
    )

    def write_nix_settings(self, f, module_settings: ModuleSettings, priority: int):
        f.write(f"  imports = [\n")
        f.write(f"    inputs.thymis.nixosModules.thymis-controller\n")
        f.write(f"  ];\n")
        f.write("  services.thymis-controller.enable = true;\n")

        return super().write_nix_settings(f, module_settings, priority)


class ThymisDevice(modules.Module):
    displayName: str = "Thymis Device"

    device_type = models.Setting(
        name="thymis.config.device-type",
        type=models.SelectOneType(
            select_one=[
                "generic-x86_64",
                "raspberry-pi-3",
                "raspberry-pi-4",
                "raspberry-pi-5",
                "generic-aarch64",
            ]
        ),
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

    authorized_keys = models.Setting(
        name="ssh.authorizedKeys",
        type=models.ListType(
            settings={
                "key": models.Setting(
                    type="string",
                    default="",
                    description="The authorized key.",
                    example="ssh-rsa AAAA...",
                )
            },
            element_name="options.nix.ssh.authorizedKey",
        ),
        default=None,
        description="The authorized keys for the SSH server.",
        example="",
        order=60,
    )

    def write_nix_settings(self, f, module_settings: ModuleSettings, priority: int):
        device_type = (
            module_settings.settings["device_type"]
            if "device_type" in module_settings.settings
            else self.device_type.default
        )

        authorized_keys = (
            module_settings.settings["authorized_keys"]
            if "authorized_keys" in module_settings.settings
            else self.authorized_keys.default
        )

        if device_type:
            f.write(f"  imports = [\n")
            f.write(f"    inputs.thymis.nixosModules.thymis-device-{device_type}\n")
            f.write(f"  ];\n")

        if authorized_keys:
            key_list = convert_python_value_to_nix(
                list(map(lambda x: x["key"] if "key" in x else None, authorized_keys)),
                ident=1,
            )
            f.write(
                f"  users.users.root.openssh.authorizedKeys.keys = lib.mkOverride {priority} {key_list};\n"
            )

        return super().write_nix_settings(f, module_settings, priority)
