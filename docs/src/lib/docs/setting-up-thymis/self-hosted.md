# Self Hosted / On-Prem

While not as easy to set up and use as the [Thymis Cloud](thymis-cloud.md), Thymis can also be self-hosted on your own hardware or in a private cloud.
This is useful for development purposes, testing, and scenarios where data privacy is a concern.

We recommend using [NixOS](self-hosted/nixOS.md) for self-hosting Thymis, as it provides a simple and reproducible way to set up the Thymis Controller and its dependencies.
If you prefer to use a containerized approach, you can also use the [OCI-Container / Docker](self-hosted/oci-container.md) setup in the future, which will allow you to run Thymis in a Docker container.

In any case, ensure that you have the necessary hardware and network setup to run Thymis, as it requires a stable connection to the devices it manages, and publicly available Domain for the Thymis Controller to allow devices to connect to it.
Since Thymis builds device images, it also requires sufficient storage space for the device images and artifacts.

## See also

[Administration](../reference/administration.md) for more information on how to manage Thymis in a self-hosted environment.
