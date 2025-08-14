# Troubleshooting

## Device doesn't connect

- Verify network credentials; make sure the Wi‑Fi SSID and password are correct.
- Temporarily switch to LAN if you have a port available.
- Connect a keyboard, mouse, and display and log in with `root` and the Root Password set in the Core Device Configuration. Inspect logs with:
  ```bash
  journalctl -xe
  ```

## Display shows old state

Changes to the i3 configuration may not automatically refresh the display.
You can refresh the display by either:

- Restarting the display manager: `systemctl restart display-manager.service`
- Restarting the device entirely

## Resolution is wrong

- Use display mode with format `1920x1080_60` or `1920x1080`.

## External modules are not being detected

If you change [external modules](../reference/concepts/repositories.md) or adjust their URL, changes may not be picked up by the hot reload.

- Restart the Thymis Controller
- Ensure the Controller has access to the external module
