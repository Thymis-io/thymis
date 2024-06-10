import pathlib
from typing import Optional

from thymis_controller import lib, models, modules


class ScreenshotModuleNotAvaliable(modules.Module):
    # kiosk_url: Setting = Setting(
    #     name="kiosk.url",
    #     type="string",
    #     default="https://example.com",
    #     description="The URL to display in kiosk mode.",
    #     example="https://example.com",
    # )
    image: str

    def write_nix_settings(
        self, f, module_settings: models.ModuleSettings, priority: int
    ):
        f.write(f'  hardware.raspberry-pi."4".fkms-3d.enable = true;\n')
        f.write(
            f"""
services.xserver.displayManager.sddm.enable = true;
services.xserver.displayManager.autoLogin.enable = true;
services.xserver.displayManager.autoLogin.user = "nixos";
services.xserver.windowManager.i3.enable = true;
services.xserver.windowManager.i3.configFile = lib.mkForce (pkgs.writeText "i3-config" ''
# i3 config file (v4)
bar {{
    mode invisible
}}
exec echo 1
exec "/run/current-system/sw/bin/xrandr --newmode 1024x600_60.00  48.96  1024 1064 1168 1312  600 601 604 622  -HSync +Vsync"
exec echo 2
exec "/run/current-system/sw/bin/xrandr --addmode HDMI-1 1024x600_60.00"
exec echo 3
exec "/run/current-system/sw/bin/xrandr --output HDMI-1 --mode 1024x600_60.00"
exec echo 4
exec "/run/current-system/sw/bin/xset s off"
exec "/run/current-system/sw/bin/xset s off"
exec "/run/current-system/sw/bin/xset -dpms"
exec "${{pkgs.unclutter}}/bin/unclutter"
# exec ${{pkgs.firefox}}/bin/firefox
exec ${{pkgs.firefox}}/bin/firefox --kiosk {self.image}
'');
        """
        )
        f.write(
            f"  systemd.services.display-manager.restartIfChanged = lib.mkForce true;\n"
        )
        f.write(
            f'  systemd.services.display-manager.environment.NONCE = "{self.image}";\n'
        )


class Grafana1Module(ScreenshotModuleNotAvaliable):
    displayName: str = "Grafana"
    icon: Optional[str] = lib.read_into_base64(
        # "./thymis_controller/icons/Grafana.svg"
        pathlib.Path(__file__).parent
        / "icons/Grafana.svg"
    )
    image: str = "${inputs.thymis}/controller/thymis_controller/modules/grafana1.png"


class MqttxModule(ScreenshotModuleNotAvaliable):
    displayName: str = "Mqttx"
    icon: Optional[str] = lib.read_into_base64(
        # "./thymis_controller/icons/mqttx.png"
        pathlib.Path(__file__).parent
        / "icons/mqttx.png"
    )
    image: str = "${inputs.thymis}/controller/thymis_controller/modules/mqttx.png"


class NodeRedModule(ScreenshotModuleNotAvaliable):
    displayName: str = "Node-RED Configured"
    icon: Optional[str] = lib.read_into_base64(
        # "./thymis_controller/icons/Node-RED.svg"
        pathlib.Path(__file__).parent
        / "icons/Node-RED.svg"
    )
    image: str = "${inputs.thymis}/controller/thymis_controller/modules/node_red.png"
