# Accessing the Thymis project git repository

In Thymis, your project is backed by a Git repository that contains all the necessary files to manage your devices, configurations, and modules.
This repository is referred to as the [Project Repository](../reference/concepts/project-repository.md).

It is automatically created when you set up your Thymis Controller and is used to store the state of your devices, configurations, and modules.

Accessing the project repository allows you to inspect the generated Nix expressions, Thymis modules, and other resources that are used in your Thymis project. This is useful when developing custom modules or when you want to understand how Thymis manages your devices and configurations.

## With access to the Thymis Controller (self-hosted Thymis instance)

The project repository is located at `/var/lib/thymis/repository` on the Thymis Controller.
You can access it using any Git client or by cloning it directly:

```bash
git clone /var/lib/thymis/repository
```

## With access to Thymis Cloud

If you are using Thymis Cloud, you can access your project repository by downloading the project archive from the Thymis Cloud UI.
This archive contains the project repository in the `/repository` directory.

## Using the Thymis project repository

Navigate to the directory where you cloned the repository or extracted the project archive.
You will find the structure described in the [Project Repository](../reference/concepts/project-repository.md) documentation.

In this directory, you can run Nix commands to build or deploy your project, inspect the generated Nix expressions, and modify the Thymis modules as needed.

Example commands you can run in the project repository directory:

```bash
nix flake update  # Update the inputs of the project
nix build .#my-device  # Build the configuration for a specific device
nix flake show  # Show the outputs of the project
nix repl # Start a Nix REPL
nix eval .#nixosConfigurations.my-device.config.networking.hostName  # Evaluate a specific Nix expression
```

## See also

- [Project Repository](../reference/concepts/project-repository.md) for more information on the structure and contents of the project repository.
