# Usage

Before diving into specific features, make sure that your Thymis setup is up and running. If you haven’t already, please refer to the [Getting Started guide](getting_started) to set up the Thymis environment and install necessary dependencies.

## Scenarios

### 1. Provisioning a New Device
Provisioning devices is at the core of Thymis. This involves creating a disk or SD card image with your desired NixOS configuration and deploying it to your target devices. Detailed steps can be found in the [Provisioning a new device](usage/provisioning) section.

### 2. Adding an Existing NixOS Device (Currently Unavailable)
If you already have a NixOS device that you want to manage with Thymis, you can easily add it to the Thymis controller. This allows you to monitor and update the device configuration remotely. Learn how to add an existing device in the [Adding an existing NixOS device](usage/existing_device) (unavailable, will 404) guide.

### 3. System Configuration
Thymis leverages NixOS’s declarative configuration, making it easy to manage and update device settings consistently. Learn more about setting up and modifying your device configurations in the [System Configuration](usage/system_configuration) guide.

### 4. Terminal Usage
For more advanced control, you can directly interact with your devices via the terminal interface. This section provides instructions on how to access your devices remotely, execute commands, and troubleshoot issues using terminal commands. More details are available in the [Terminal Usage](usage/terminal) guide.

### 5. VNC Usage
Thymis supports remote graphical access to your devices using VNC. This feature is useful when you need to interact with a device’s GUI remotely. The [VNC Usage](usage/vnc) section explains how to set up and use VNC for your devices.

## Tips for Effective Use

- **Regular Updates**: Regularly check for updates to Thymis and its modules to ensure that your deployments benefit from the latest features and security patches.
- **Device Grouping**: Use the device tagging feature to group similar devices, which makes managing large fleets of devices more straightforward.

## Additional Resources

- **Extensions (Under Development)**: If you're interested in expanding Thymis’s capabilities, head to the [Extensions](extensions) section to learn how to create and integrate custom extensions.
- **API Documentation**: For developers looking to interact with Thymis programmatically, the [API](api) page provides detailed information on available endpoints and how to use them.
