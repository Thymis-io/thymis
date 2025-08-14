# OCI-Container / Docker (coming soon)

Thymis will soon support running in an OCI-Container or Docker container, allowing for more flexible and portable deployment options. This setup will enable you to run the Thymis Controller within a container, making it easier to deploy and manage Thymis on various platforms.

## Current Status
This functionality is currently in development and not yet supported. When available, it will be similar to the existing NixOS deployment but with Docker-compatible packaging.

## Important Note: Running Docker on Managed Devices

If your goal is to run Docker containers on your Thymis-managed devices (rather than containerizing the Thymis Controller itself), this is already supported through the built-in **OCI-Containers module**.

The [OCI-Containers module](../../external-projects/thymis-modules.md#oci-containers) allows you to:
- Deploy and manage Docker containers on your devices
- Configure container networking and storage
- Define which applications run in containers

This module is production-ready and can be added directly to your device configurations or tags to enable containerized applications on your devices.

## See Also

- [Self-hosted setup](../self-hosted.md) for alternative deployment options
- [NixOS self-hosting](nixOS.md) for the current recommended setup
- [OCI-Containers module](../../external-projects/thymis-modules.md#oci-containers) for deploying Docker on devices
- [Administration](../../reference/administration.md) for managing a running Thymis instance

When the container deployment option becomes available, this page will be updated with detailed instructions for setting up and running Thymis in a container environment.
