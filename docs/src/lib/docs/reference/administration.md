# Administration

In order to properly administer a running Thymis Controller instance or a project deployed using Thymis, you need to understand it's architecture and how the different components interact with each other.

## Architecture (Thymis Controller)

Thymis is built around a central controller that manages devices, configurations, and deployments.
The controller is responsible for handling device connections, storing configurations, and managing deployments.
The controller opens a port for the HTTP Proxy to expose the Thymis UI and API, which can be accessed by users and devices.
The Thymis UI is a Web-Application that allows users to interact with the Thymis Controller, manage devices, configurations, and deployments, which is served by the Thymis controller.

The controller also manages the project repository, which contains the Nix Flakes and Thymis Modules used to define device configurations and deployments.

Usually, the Thymis Controller is run as a system service, which allows it to start automatically on boot and run in the background.
The working directory of the Thymis Controller is `/var/lib/thymis` by default, and contains the [project repository](concepts/project-repository.md) at `/var/lib/thymis/repository`, and the database at `/var/lib/thymis/thymis.sqlite`.
An SSH Private-Public Key pair is also at `/var/lib/thymis/id_thymis{.pub,}` which is used to authenticate to devices.
Images for devices are stored in `/var/lib/thymis/images`.
The controller also uses a SQLite database to store information about devices, configurations, deployments, secrets, and other metadata.

## Architecture (Devices)

Thymis devices run a lightweight agent called the Thymis Agent, which is responsible for connecting to the Thymis Controller and managing deployments.
The Thymis Agent is a Python application that runs on the device and communicates with the Thymis Controller over a WebSocket connection.

It only requires an outbound HTTP(S) connection to the Thymis Controller at `https://A_CUSTOM_DOMAIN.thymis.cloud` (or the domain you configured for your Thymis Controller).
The Thymis Agent is responsible for:
- Connecting to the Thymis Controller and authenticating itself using it's SSH Public Host Key.
- Receiving new configurations and deployments from the Thymis Controller.
- Applying the configurations and deployments to the device.
- Reporting the status of the device back to the Thymis Controller.


## Configuration

When setting up the Thymis Controller on your own infrastructure, you need to configure your network for the controller to be available to devices and users, as well as outbound connections to function properly.
The controller needs to be reachable by devices, so you need to set up a publicly available domain name for the controller.
This domain name should be configured in the Thymis Controller configuration, which is usually done in the NixOS configuration file.

Available configuration options are described in the [Thymis NixOS module documentation](../setting-up-thymis/self-hosted/nixOS.md) and can be set in the NixOS configuration file.

See [Firewall](administration/firewall.md) for more information on how to configure the firewall for the Thymis Controller.
