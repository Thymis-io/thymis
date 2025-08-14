# Creating your first Thymis module

This guide walks you through creating your first custom Thymis module — a temperature logger that simulates sensor readings and writes them to a log file.

## Step 1: Create the Module File

Create a Python file named `temperature_logger.py` in a directory with the structure:

```
my-thymis-project/
├── README.md (must contain "contains thymis modules")
└── my_project_name/
    ├── __init__.py
    └── temperature_logger.py
```

File content:

```python
from thymis_controller.modules.modules import Module, Setting, LocalizedString
from thymis_controller.project import Project
from thymis_controller import models
import pathlib

class TemperatureLoggerModule(Module):
    display_name: LocalizedString = "Temperature Logger"

    # Module settings
    log_file = Setting(
        display_name="Log File Path",
        type="string",
        default="/var/log/temp.log",
        description="Where to store temperature logs"
    )

    interval = Setting(
        display_name="Logger Interval (seconds)",
        type="int",
        default=60,
        description="Time between readings"
    )

    unit = Setting(
        display_name="Temperature Unit",
        type="string",
        default="°C",
        description="Display unit for temperature"
    )

    def write_nix_settings(self, f, path, module_settings, priority, project: Project):
        # Extract configured settings with fallback to defaults
        log_file = module_settings.settings.get("log_file", self.log_file.default)
        interval = module_settings.settings.get("interval", self.interval.default)
        unit = module_settings.settings.get("unit", self.unit.default)

        # Create Python script using Nix's writePython3 helper
        script = (
            "import time\n"
            "from datetime import datetime\n"
            "from random import uniform\n\n"
            "while True:\n"
            "    temp = uniform(20.0, 30.0)\n"
            "    timestamp = datetime.now().isoformat()\n"
            f"    with open('{log_file}', 'a') as f:\n"
            f"        f.write(f\"{{timestamp}} Temperature: {{temp:.2f}}{unit}\\n\")\n"
            f"    time.sleep({interval})\n"
        )

        # Generate NixOS configuration
        f.write(
            "systemd.services.temperature-logger = {\n"
            "  description = \"Temperature Logger\";\n"
            "  wantedBy = [\"multi-user.target\"];\n"
            "  serviceConfig = {\n"
            f"    ExecStart = pkgs.writers.writePython3 \"temp_logger\" {{}} ''{script}'';\n"
            "    Restart = \"always\";\n"
            "  };\n"
            "};\n"
        )
```

## Part Breakdown

### Module Structure

- **Imports** — required base classes and helper functions.
- **Settings** — exposed configurations in the Thymis UI.
- **`write_nix_settings`** — generates:
  1. Python logger script.
  2. `systemd` service configuration.

### Setting Types

| Setting    | Type    | Purpose                      |
| ---------- | ------- | ---------------------------- |
| `log_file` | string  | Output file path             |
| `interval` | integer | Seconds between measurements |
| `unit`     | string  | Temperature unit symbol      |

### Generated Infrastructure

- Persistent **systemd service** using [`writePython3`](https://github.com/NixOS/nixpkgs/blob/master/pkgs/build-support/writers/scripts.nix)
- Random temperature simulation (20‑30 °C range)
- ISO‑timestamped log entries

## Step 2: Add the Repository to Thymis

1. Upload your module repository to GitHub/GitLab.
2. In Thymis UI: **External Repositories → Add Repository**.
3. Enter your repository URL.

## Step 3: Add the Module to Devices

1. Create a new configuration or edit an existing one.
2. **+ Add Module → Select "Temperature Logger"**.
3. Configure settings:
   - Set log file path (`/var/log/temps.log`)
   - Adjust interval (e.g., 120 seconds)
4. **Commit → Deploy**

## Step 4: Verify Operation

Access the device via [terminal](../../device-lifecycle/ssh-terminal.md):

```bash
# Check service status
systemctl status temperature-logger

# View logs
tail -f /var/log/temp.log
# Sample output:
# 2025-03-15T14:32:18.12345 Temperature: 24.71°C
```

## Next Steps

- Make parameters configurable via [tags](../../device-lifecycle/tags.md).
- Add [secret authentication](../../device-lifecycle/secrets.md) for remote APIs.
- Create [dashboard integrations](python-language-module.md).
- Review the **[Full Module Class API Reference](../../reference/concepts/module.md)** for advanced capabilities like `register_secret_settings`, custom setting types, and icon embedding.

> **Tip:** For physical sensors, replace the random number generator with hardware interface libraries like `gpiozero` or `Adafruit_DHT` in your Python script. Just add required packages to your NixOS configuration!
