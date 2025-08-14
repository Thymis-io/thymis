# How to add VNC to my (custom) modules and applications

This guide explains how to enable VNC support in your Thymis-managed devices, either through the built-in Kiosk module or by adding VNC capabilities to custom modules and applications.

## Using the Built-in Kiosk Module with VNC

The simplest way to enable VNC is by using the built-in Kiosk module:

1. **Add the Kiosk module** to your device configuration or tag
2. **Enable VNC support** in the module settings:
   - Set `Enable VNC Server` to true
   - Optionally set a VNC password

3. **Deploy the configuration** to your devices

Once deployed, you can access VNC through:
- The **VNC tab** in the device configuration page
- Live view of the device's screen
- Remote control by checking **Control Device**

## Adding VNC to Custom Modules

### Detection Logic

Thymis automatically shows VNC controls when:
- A module type contains "vnc" (case-insensitive)
- The Kiosk module is enabled with VNC
- A custom module has "vnc" in its JSON configuration

### Enabling VNC in Custom Nix Modules

For custom Nix modules, you can set up a VNC server:

```nix
{ pkgs, config, ... }:

{
  services.xserver.enable = true;
  services.xserver.displayManager.sddm.enable = true;

  services.xvfb.enable = true;
  services.xvfb.screen = 0;

  # Install and configure a VNC server
  environment.systemPackages = [ pkgs.tigervnc ];

  systemd.services.vncserver = {
    description = "VNC Server";
    after = [ "network.target" "xvfb.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      User = "thymiskiosk";
      ExecStart = "${pkgs.tigervnc}/bin/vncserver :1 -geometry 1920x1080 -depth 24";
      ExecStop = "${pkgs.tigervnc}/bin/vncserver -kill :1";
    };
  };
}
```

### Enabling VNC in Custom Python Modules

For custom Python modules, ensure your module configuration includes:

```python
class MyVNCModule(Module):
    display_name = "My VNC Application"

    enable_vnc = Setting(
        display_name="Enable VNC",
        type="bool",
        default=False
    )

    vnc_password = Setting(
        display_name="VNC Password",
        type="secret",
        default="password"
    )

    def write_nix_settings(self, f, path, settings, priority, project):
        if settings.get("enable_vnc", False):
            password = settings.get("vnc_password", self.vnc_password.default)
            f.write(f'''
            services.xserver.enable = true;
            services.xvfb.enable = true;
            environment.systemPackages = [ pkgs.tigervnc ];
            systemd.services.vncserver = {{
                description = "VNC Server";
                after = [ "network.target" "xvfb.service" ];
                wantedBy = [ "multi-user.target" ];
                serviceConfig = {{
                    User = "thymiskiosk";
                    ExecStart = "${{pkgs.tigervnc}}/bin/vncserver :1 -geometry 1920x1080 -depth 24";
                    ExecStop = "${{pkgs.tigervnc}}/bin/vncserver -kill :1";
                }};
            }};
            ''')
```

## Security Considerations

- Always set a strong VNC password
- Consider using SSH tunneling for additional security
- Limit VNC access to specific IP addresses when possible
- Regularly rotate VNC passwords

## Troubleshooting

- **VNC not appearing**: Check that your module meets the detection criteria
- **Connection issues**: Verify firewall settings and network connectivity
- **Password not working**: Ensure the password is correctly set and deployed
- **Black screen**: Check display configuration and X server settings

## Related Resources

- [Setting up a Kiosk with VNC](../../device-lifecycle/kiosk.md)
- [Accessing the Terminal](../../device-lifecycle/ssh-terminal.md)
- [Troubleshooting](../../device-lifecycle/troubleshooting.md)
