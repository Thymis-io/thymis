# Test your configuration with VMs

Thymis allows you to test your device configurations using virtual machines (VMs). This is particularly useful for development and testing without needing physical hardware.

## Prerequisites

- Ensure you have the Thymis Controller running on an x86 system.
- Your device configuration should be set up for a generic x86 device type.
- The machine running the Thymis Controller should have virtualization support enabled (e.g., KVM on Linux).

## Setting up a VM

1. Create or select a device configuration for a generic x86 device type
2. In the configuration, select "NixOS VM" as the image format
3. Click the "Start VM" button instead of "Download Device Image"
4. Wait for the task to complete - this will launch a virtual machine with your configuration

## Using the VM

Once started, the VM will:
- Automatically connect to the Thymis Controller
- Appear in the Devices list just like a physical device
- Allow you to test deployments, updates, and configurations
- Provide the same terminal access and monitoring options as physical devices

## Benefits of VM testing

- **Rapid prototyping**: Test configurations without flashing hardware
- **Development cycle**: Quickly iterate on module changes
- **Troubleshooting**: Isolate issues between hardware and software
- **CI/CD integration**: Automate testing in your development workflow

## Limitations

- VM performance may differ from physical hardware
- Not all hardware features (GPIO, specific peripherals) are available
- For production deployment, always test on target hardware

## See also
- [Getting started with devices](getting-started.md)
- [Deploy an Update](update.md)
- [Accessing the Terminal](ssh-terminal.md)
