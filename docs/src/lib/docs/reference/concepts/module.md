# Thymis Module

A Thymis Module is a reusable component that defines configurations, settings, and behaviors for devices managed by Thymis. Modules form the building blocks of device configurations, allowing you to package software, define system settings, and manage deployments in a declarative manner.

## Module Structure

All Thymis modules inherit from the base `Module` class and define a set of settings and configuration options. Here's the basic structure:

```python
from thymis_controller.modules.modules import Module, Setting, LocalizedString

class MyModule(Module):
    display_name: LocalizedString = "My Module"

    # Define settings
    my_setting = Setting(
        display_name=LocalizedString(en="My Setting", de="Meine Einstellung"),
        type="string",
        default="default_value",
        description=LocalizedString(en="A description of the setting", de="Eine Beschreibung der Einstellung"),
    )
```

### Module Properties

- **`display_name`**: Name of the module that appears in the UI. Can be a string or a `LocalizedString` for internationalization.
- **`icon`**: Optional base64 encoded icon for light theme.
- **`icon_dark`**: Optional base64 encoded icon for dark theme.

### Setting Types

Modules define settings using the `Setting` class, which supports various types:

```python
# Simple setting types
Setting(type="string")      # Text input
Setting(type="int")         # Number input
Setting(type="bool")        # Checkbox
Setting(type="textarea")    # Multi-line text input

# Complex types
Setting(type=SelectOneType(...))    # Dropdown selection
Setting(type=ListType(...))         # List of items
Setting(type=SecretType(...))       # For sensitive data
Setting(type=ArtifactType())        # For file artifacts
```

## Overridable Functions

Modules can override several functions to customize their behavior:

### write_nix_settings

Generates Nix configuration based on module settings:

```python
def write_nix_settings(self, f, path, module_settings, priority, project):
    # Access settings
    my_value = module_settings.settings.get("my_setting", self.my_setting.default)

    # Generate Nix configuration
    f.write(f"  my_nix_option = {convert_python_value_to_nix(my_value)};")
```

### register_secret_settings

Registers secrets that need to be managed securely:

```python
def register_secret_settings(self, module_settings, project):
    secret_settings = []
    if "password" in module_settings.settings:
        secret_settings.append((self.password.type, module_settings.settings["password"]))
    return secret_settings
```

## Localization

Module names, settings, and descriptions support localization using `LocalizedString`:

```python
display_name = LocalizedString(
    en="My Module",
    de="Mein Modul",
    fr="Mon Module"
)

my_setting = Setting(
    display_name=LocalizedString(
        en="My Setting",
        de="Meine Einstellung"
    ),
    type="string",
    description=LocalizedString(
        en="A useful setting",
        de="Eine nützliche Einstellung"
    )
)
```

## Including Icons

Icons can be any image format (SVG, PNG, etc.) and should be embedded as base64 encoded strings:

```python
icon: str = read_into_base64(
    str(pathlib.Path(__file__).parent / "icons" / "module-icon.svg")
)
```

## Example: Simple Kiosk Module

Here's a complete example module that creates a basic kiosk configuration:

```python
import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.lib import read_into_base64
from thymis_controller.project import Project
import pathlib

class KioskModule(modules.Module):
    display_name: str = "Simple Kiosk"

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "display.svg")
    )

    kiosk_url = modules.Setting(
        display_name="Kiosk URL",
        type="string",
        default="https://example.com",
        description="The URL to display in kiosk mode",
    )

    fullscreen = modules.Setting(
        display_name="Fullscreen",
        type="bool",
        default=True,
        description="Launch browser in fullscreen mode",
    )

    def write_nix_settings(
        self,
        f,
        path,
        module_settings: models.ModuleSettings,
        priority: int,
        project: Project,
    ):
        kiosk_url = (
            module_settings.settings["kiosk_url"]
            if "kiosk_url" in module_settings.settings
            else self.kiosk_url.default
        )

        fullscreen = (
            module_settings.settings["fullscreen"]
            if "fullscreen" in module_settings.settings
            else self.fullscreen.default
        )

        fullscreen_arg = "--kiosk" if fullscreen else ""

        f.write(
            f"""
            services.xserver.enable = lib.mkOverride {priority} true;
            services.displayManager.sddm.enable = lib.mkOverride {priority} true;
            services.displayManager.autoLogin.enable = lib.mkOverride {priority} true;
            services.displayManager.autoLogin.user = "thymiskiosk";
            users.users.thymiskiosk = {{
                isNormalUser = true;
                createHome = true;
            }};
            services.xserver.windowManager.i3.enable = lib.mkOverride {priority} true;
            services.xserver.windowManager.i3.configFile = lib.mkOverride {priority} (pkgs.writeText "i3-config" ''
            exec "{pkgs.chromium}/bin/chromium {fullscreen_arg} '{kiosk_url}'"
            '');
            """.strip()
        )
```

## Working with Complex Settings

For more complex configurations like device settings, you might use nested list types:

```python
device_settings = modules.Setting(
    display_name="Device Configuration",
    description="Configure device-specific parameters",
    type=modules.ListType(
        settings={
            "interface": modules.Setting(
                display_name="Network Interface",
                type="string",
            ),
            "ip_address": modules.Setting(
                display_name="IP Address",
                type="string",
            ),
            "subnet": modules.Setting(
                display_name="Subnet",
                type="string",
            ),
        },
        element_name="Network Interface"
    )
)
```

## Source Code

The module system is implemented in the [controller/thymis_controller/modules/modules.py](https://github.com/Thymis-io/thymis/blob/master/controller/thymis_controller/modules/modules.py) file, which defines the base `Module` class and setting types.

## See Also:
- [Device Configuration](configuration.md)
- [Secrets](secrets.md)
- [Artifacts](artifacts.md)
- [External Repositories](../../external-projects/external-repositories.md)
