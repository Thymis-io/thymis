import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller.lib import read_into_base64


class Kiosk(modules.Module):
    display_name: str = "Kiosk"

    category = modules.LocalizedString(
        en="Applications",
        de="Anwendungen",
    )

    description = modules.LocalizedString(
        en="Display a single website fullscreen in a locked-down browser.",
        de="Eine einzelne Website im Vollbild in einem gesperrten Browser anzeigen.",
    )

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "Display.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "Display_dark.svg")
    )

    settings_namespace = "kiosk"

    kiosk_url = modules.Setting(
        nix_attr_name="thymis.config.kiosk.url",
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
        nix_attr_name="thymis.config.kiosk.xrandr-mode",
        display_name=modules.LocalizedString(
            en="Display mode",
            de="Bildschirmmodus",
        ),
        type="string",
        default="1920x1080",
        description="xrandr mode.",
        example="1920x1080",
        order=40,
    )

    xrandr_rotation = modules.Setting(
        nix_attr_name="thymis.config.kiosk.xrandr-rotation",
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
        nix_attr_name="thymis.config.kiosk.volume",
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

    audio_sink_fuzzy = modules.Setting(
        nix_attr_name="thymis.config.kiosk.audio-sink-fuzzy",
        display_name=modules.LocalizedString(
            en="Audio Sink",
            de="Audio Sink",
        ),
        type="string",
        default="",
        description="Select the audio sink via a fuzzy search. Eg. 'audio' or 'hdmi' can be used to match the default output or HDMI on a Raspberry Pi 3.\nTo list available sinks, the following commands can be used on the device:\n> machinectl shell thymiskiosk@.host\n> pactl list short sinks",
        example="HDMI",
        order=57,
    )

    enable_vnc = modules.Setting(
        nix_attr_name="thymis.config.kiosk.enable-vnc",
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
        nix_attr_name="thymis.config.kiosk.vnc-password",
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
