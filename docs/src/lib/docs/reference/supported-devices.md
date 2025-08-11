# Supported Devices

Thymis comes with built-in support for the following devices:
- Raspberry Pi 3
- Raspberry Pi 4
- Raspberry Pi 5
- Generic x86 devices
- Generic ARM devices

Adding support for additional devices is straightforward and can be done by writing Nix code. Thymis leverages NixOS options, making it easy to target both `aarch64` (ARM 64-bit) and `x86_64` (Intel/AMD 64-bit) architectures.

To add support for a new device type, see the [Adding a new Type of Device](../external-projects/add-new-device-type.md) guide.

If your hardware is compatible with NixOS, you can usually add support by specifying the correct system architecture and options in your configuration using a [Custom NixOS Module](../external-projects/thymis-modules/nix-language-module.md).
