# Deployment

After a device has been flashed for the first time, it connects to the Thymis Controller.
It exchanges it's SSH public host key and the Thymis Controller verifies and stores it.
This creates a **Deployment** for the device.

The **Deployment** stores information about the deployed [configuration](configuration.md) and the commit of the project repository that the device is running.

Software updates or configuration changes can now be deployed in different ways:

**Over-the-Air (OTA) updates**
- Incremental updates that only transfer modified system changes
- Atomic switching to new configurations after successful update
- Minimal downtime and bandwidth usage
- Automatic rollback on failure detection

**Full Image Replacement**
- Complete system replacement for air-gapped environments or recovery scenarios
- Manual installation process

## Reliability and Recovery

If an OTA update breaks the system and the device cannot reconnect to the controller again, the previous configuration will be rolled back automatically.
