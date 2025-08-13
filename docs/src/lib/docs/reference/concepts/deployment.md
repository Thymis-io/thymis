# Deployment

After a device has been flashed for the first time, it connects to the Thymis Controller.
It exchanges it's SSH public host key and the Thymis Controller verifies and stores it.
This creates a **Deployment** for the device.

The **Deployment** stores information about the deployed [configuration](configuration.md) and the commit of the project repository that the device is running.
