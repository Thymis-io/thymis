# Using the Python language module (coming soon)

We are working on a dedicated **Python Language Module** for Thymis.
Once available, you’ll be able to write and run Python code on your devices directly from the Thymis UI — including dependency handling, service setup, and configuration — without dropping into a custom Nix expression.

Until then, you can still achieve the same effect by using the existing **[Custom Nix Language Module](nix-language-module.md)** and embedding your Python code in a Nix expression.

## Temporary workaround

In your device or tag, add a [**Custom NixOS Module**](nix-language-module.md) and use [`pkgs.writers.writePython3`](https://github.com/NixOS/nixpkgs/blob/6797403cbe8d8581c60104dc08a670229ab26c39/pkgs/build-support/writers/scripts.nix#L1262) to build a Python script into the system, then run it via a `systemd` service.

Here’s an example that:
- Uses **PyYAML** to parse a configuration file.
- Simulates reading a temperature value.
- Logs readings to `/var/log/temperature.log` every minute.

```nix
systemd.services.temperature-logger = let
# Build a Python script with PyYAML
  temperatureLogger = pkgs.writers.writePython3 "temperature_logger" {
    libraries = [ pkgs.python3Packages.pyyaml ];
  } ''
    import yaml
    import time
    from datetime import datetime
    from random import uniform

    # Example YAML config (could also come from a file)
    config_yaml = """
    log_file: "/var/log/temperature.log"
    unit: "°C"
    """
    config = yaml.safe_load(config_yaml)

    while True:
        temperature = round(uniform(18.0, 25.0), 2)
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} Temperature: {temperature}{config['unit']}\n"

        with open(config["log_file"], "a") as f:
            f.write(log_entry)

        print(f"Logged: {log_entry.strip()}")
        time.sleep(60)  # wait 1 minute
  '';
in {
  description = "Temperature Logger Example (Python)";
  wantedBy = [ "multi-user.target" ];
  serviceConfig = {
    ExecStart = "${temperatureLogger}";
    Restart = "always";
  };
};
```

When deployed:
- Nix will build your Python script and include PyYAML as a dependency.
- Systemd will run it automatically and restart it if it stops.
- Output gets logged to `/var/log/temperature.log` and is also visible in `journalctl -u temperature-logger`.

---

## Roadmap

When the Python Language Module ships, you’ll be able to:
- Write Python code directly in the UI without a full Nix block.
- Pick dependencies from `python3Packages` via a form.
- Choose how it runs: oneshot script, background daemon, or on‑demand.
- Reuse scripts easily across tags and device configurations.

---

**Until then**:
Use the [Custom Nix Language Module](nix-language-module.md) + `pkgs.writers.writePython3` to run Python scripts on your devices today.
