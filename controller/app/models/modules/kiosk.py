from app.models import Module, Setting
from app.models.setting import ModuleSettings


class Kiosk(Module):
    kiosk_url: Setting = Setting(
        name="kiosk.url",
        type="string",
        default="https://example.com",
        description="The URL to display in kiosk mode.",
        example="https://example.com",
    )

    def write_nix_settings(self, f, module_settings: ModuleSettings, priority: int):
        kiosk_url = (
            module_settings.settings["kiosk.url"].value
            if "kiosk.url" in module_settings.settings
            else self.kiosk_url.default
        )

        f.write(f'  hardware.raspberry-pi."4".fkms-3d.enable = true;')
        f.write(
            f"""
services.xserver.windowManager.i3.configFile = lib.mkForce (pkgs.writeText "i3-config" ''
# i3 config file (v4)
bar {{
    mode invisible;
}};
exec ${{pkgs.firefox}}/bin/firefox --kiosk {kiosk_url}
'');
        """
        )
        f.write(
            f"  systemd.services.display-manager.restartIfChanged = lib.mkForce true;"
        )
        f.write(
            f'  systemd.services.display-manager.environment.NONCE = "{kiosk_url}";'
        )
