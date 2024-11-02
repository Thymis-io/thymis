import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.project import Project


class Kiosk(modules.Module):
    display_name: str = "Kiosk"

    kiosk_url = modules.Setting(
        display_name=modules.LocalizedString(
            en="URL",
            de="URL",
        ),
        type="string",
        default="https://example.com",
        description="The URL to display in kiosk mode.",
        example="https://example.com",
        order=10,
    )

    xrandr_mode = modules.Setting(
        display_name=modules.LocalizedString(
            en="Display mode",
            de="Bildschirmmodus",
        ),
        type="string",
        default="1024x600_60.00",
        description="xrandr mode.",
        example="1024x600_60.00",
        order=40,
    )

    xrandr_rotation = modules.Setting(
        display_name=modules.LocalizedString(
            en="Display rotation",
            de="Bildschirmrotation",
        ),
        type=modules.SelectOneType(select_one=["normal", "left", "right", "inverted"]),
        default="normal",
        description="xrandr rotation.",
        example="normal",
        order=50,
    )

    volume = modules.Setting(
        display_name=modules.LocalizedString(
            en="Volume",
            de="Lautstärke",
        ),
        type="int",
        default=100,
        description="Volume between 0% and 100%.",
        example="100",
        order=55,
    )

    enable_vnc = modules.Setting(
        display_name=modules.LocalizedString(
            en="Enable VNC server",
            de="VNC-Server aktivieren",
        ),
        type="bool",
        default=False,
        description="Enable VNC server.",
        example="true",
        order=60,
    )

    vnc_password = modules.Setting(
        display_name=modules.LocalizedString(
            en="VNC password",
            de="VNC-Passwort",
        ),
        type="string",
        default="password",
        description="VNC password.",
        example="password",
        order=70,
    )

    def write_nix_settings(
        self, f, module_settings: models.ModuleSettings, priority: int, project: Project
    ):
        kiosk_url = (
            module_settings.settings["kiosk_url"]
            if "kiosk_url" in module_settings.settings
            else self.kiosk_url.default
        )

        enable_vnc = (
            module_settings.settings["enable_vnc"]
            if "enable_vnc" in module_settings.settings
            else self.enable_vnc.default
        )

        vnc_password = (
            module_settings.settings["vnc_password"]
            if "vnc_password" in module_settings.settings
            else self.vnc_password.default
        )

        xrandr_mode = (
            module_settings.settings["xrandr_mode"]
            if "xrandr_mode" in module_settings.settings
            else self.xrandr_mode.default
        )

        xrandr_rotation = (
            module_settings.settings["xrandr_rotation"]
            if "xrandr_rotation" in module_settings.settings
            else self.xrandr_rotation.default
        )

        volume = (
            module_settings.settings["volume"]
            if "volume" in module_settings.settings
            else self.volume.default
        )

        volume = max(0, min(100, int(volume)))

        nonce = hash(str(module_settings.__dict__))

        f.write(
            f"""
            services.xserver.enable = lib.mkOverride {priority} true;
            services.displayManager.sddm.enable = lib.mkOverride {priority} true;
            services.displayManager.autoLogin.enable = lib.mkOverride {priority} true;
            services.displayManager.autoLogin.user = lib.mkOverride {priority} "thymiskiosk";
            users.users.thymiskiosk = lib.mkOverride {priority} {{
                isNormalUser = true;
                createHome = true;
            }};
            boot.kernelParams =
              let
                kernelParams = {{
                  # see https://github.com/NixOS/nixos-hardware/issues/703#issuecomment-1869075978
                  "raspberry-pi-4" = [ "snd_bcm2835.enable_headphones=1" "snd_bcm2835.enable_hdmi=1" ];
                }};
              in
              lib.mkIf (builtins.hasAttr config.thymis.config.device-type kernelParams) kernelParams.${{config.thymis.config.device-type}};
            boot.initrd.kernelModules =
              let
                kernelModules = {{
                  "raspberry-pi-3" = [ "vc4" "bcm2835_dma" "i2c_bcm2835" ];
                }};
              in
              lib.mkIf (builtins.hasAttr config.thymis.config.device-type kernelModules) kernelModules.${{config.thymis.config.device-type}};
            hardware.pulseaudio.enable = lib.mkIf (config.thymis.config.device-type == "raspberry-pi-3" || config.thymis.config.device-type == "raspberry-pi-4") true;
            hardware.pulseaudio.support32Bit = true;
            services.xserver.windowManager.i3.enable = lib.mkOverride {priority} true;
            services.xserver.windowManager.i3.configFile = lib.mkOverride {priority} (pkgs.writeText "i3-config" ''
            # i3 config file (v4)
            bar {{
                mode invisible
            }}
            exec "/run/current-system/sw/bin/xrandr --newmode 1024x600_60.00  48.96  1024 1064 1168 1312  600 601 604 622  -HSync +Vsync; /run/current-system/sw/bin/xrandr --addmode HDMI-1 1024x600_60.00;"
            exec "sleep 2; /run/current-system/sw/bin/xrandr --output HDMI-1 --mode {xrandr_mode} --rotate {xrandr_rotation}"
            exec "/run/current-system/sw/bin/xset s off"
            exec "/run/current-system/sw/bin/xset -dpms"
            exec "${{pkgs.unclutter}}/bin/unclutter"
            exec ${{pkgs.chromium}}/bin/chromium --kiosk {kiosk_url} --disable-gpu
            {'exec ${pkgs.bash}/bin/bash -c "mkdir -p $HOME/tigervnc; ${pkgs.tigervnc}/bin/vncpasswd -f <<< \\"'+ vnc_password + '\\" > $HOME/tigervnc/passwd"' if enable_vnc else ''}
            {'exec ${pkgs.tigervnc}/bin/x0vncserver -display :0 -PasswordFile=$HOME/tigervnc/passwd' if enable_vnc else ''}
            exec "${{pkgs.pamixer}}/bin/pamixer --set-volume {volume}"
            '');
            systemd.services.display-manager.restartIfChanged = lib.mkOverride {priority} true;
            systemd.services.display-manager.environment.NONCE = lib.mkOverride {priority} "{nonce}";
            networking.firewall.allowedTCPPorts = [ 5900 ];
            """
        )
