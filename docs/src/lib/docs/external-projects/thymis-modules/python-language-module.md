# Using the Python language module

The **Python Language Module** for Thymis allows you to write and run Python code on your devices directly from the Thymis UI — including dependency handling, service setup, and timer configuration — without dropping into a custom Nix expression.

## How to Use the Python Module

1. **Add the module**: In your device or tag configuration, add the "Python Module" from the module list.

2. **Configure your script**: Write your Python code directly in the "Python Script" field.

3. **Set dependencies**: Add any required Python packages from `python3Packages` (e.g., `requests`, `numpy`, `pandas`).

4. **Add system packages**: Include any system packages from nixpkgs if needed (e.g., `git`, `curl`, `ffmpeg`).

5. **Configure timing**: Use the timer configuration to control when and how often your script runs.

## Module Settings

| Setting | Type | Purpose |
|---------|------|---------|
| **Timer Configuration** | SystemdTimer | Controls when the script runs (oneshot, recurring, etc.) |
| **Python Packages** | List | Python packages from `python3Packages` to include |
| **System Packages** | List | System packages from nixpkgs to include in PATH |
| **Python Script** | Code | The Python code to execute |

## Example: Temperature Logger

Here's an example that logs temperature readings every minute:

```python
import time
import json
from datetime import datetime
from random import uniform

# Configuration
log_file = "/var/log/temperature.log"
unit = "°C"

while True:
    # Simulate reading temperature
    temperature = round(uniform(18.0, 25.0), 2)
    timestamp = datetime.now().isoformat()

    # Create log entry
    log_entry = {
        "timestamp": timestamp,
        "temperature": temperature,
        "unit": unit
    }

    # Write to log file
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"Logged: {temperature}{unit} at {timestamp}")
    time.sleep(60)  # Wait 1 minute
```

### Configuration for the Example

- **Python Packages**: Add `json` if not using built-in, or any other packages like `requests` for API calls
- **Timer Configuration**: Set up as a service that starts automatically
- **System Packages**: Add any tools your script needs to call

## Benefits

The Python Module provides several advantages over manual Nix expressions:

- **User-friendly**: Write Python directly without Nix knowledge
- **Dependency management**: Easy package selection via forms
- **Service integration**: Automatic systemd service generation
- **Timer support**: Built-in scheduling capabilities
- **Reusable**: Share scripts across tags and device configurations

## Migration from Custom Nix

If you have existing Python code in a Custom Nix Module using `pkgs.writers.writePython3`, you can easily migrate:

1. Copy your Python code to the "Python Script" field
2. Add your dependencies to the "Python Packages" list
3. Configure the timer as needed
4. Remove the old Nix expression

## Advanced Usage

For complex scenarios, you can still combine the Python Module with other modules or use the Custom Nix Module for advanced systemd configurations.
