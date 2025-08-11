# Troubleshooting

## Device doesn't connect

- Verify network credentials, make sure the WiFi SSID and password are correct.
- Temporary switch to LAN, if you have a port available.
- Connect a keyboard, mouse and display and log in with root and the Root Password set in the Core Device Configuration. Now you can inspect logs with `journalctl`

## Display shows old state

The i3 config may changed without triggering a display update.
Changes to the i3 configuration may not automatically trigger a display update.
You can refresh the display by either:
- Restarting the display manager: `systemctl restart display-manager.service`
- Restarting the device entirely.

## Resolution is wrong

- use display mode with format `1920x1080_60`
