# Project repository

In Thymis, your project is backed by a Git repository that contains all the necessary files to manage your devices, configurations, and modules. This repository is referred to as the **Project Repository**.
It is automatically created when you set up your Thymis Controller and is used to store the state of your devices, configurations, and modules.

## Structure of the Project Repository

The project repository is structured as follows:

```
/var/lib/thymis/repository/
├── state.json # JSON file containing the state of the project, including devices, configurations, and modules
├── flake.nix # Generated from state.json: Nix flake file; entry point for your Nix expressions; contains the inputs and outputs of your project
├── flake.lock # Nix flake lock file; contains the pinned state of the inputs
├── hosts/ # Directory containing device configurations; one subdirectory per device
│   └── <device-name>/
│       ├── thymis_controller.modules.thymis.ThymisDevice.nix # Device configuration file
│       └── <other-module>.nix # Other Thymis modules for the device, if any
└── tags/ # Directory containing tags; one subdirectory per tag
    └── <tag-name>/
        └── <module-name>.nix # Thymis module for the tag
```

The `state.json` file contains the state of the project, including devices, configurations, and modules. It is generated from the Thymis UI and used to keep track of your project.

The `flake.nix` file is generated from `state.json` and contains the Nix expressions for your project. Every time you make changes in the Thymis UI, `flake.nix` is updated accordingly.

The `flake.lock` file pins input versions for reproducibility. It is updated using the [Update](../ui/update.md) button in the Thymis UI.

The `hosts/` directory contains device configurations, with one subdirectory per device. Each subdirectory contains the primary device configuration file and optional additional modules.

The `tags/` directory contains tag configurations, with one subdirectory per tag. Each subdirectory contains the module configuration files included in the tag.

## Accessing the Project Repository

You can access the project repository of your Thymis Controller as described in [Accessing the Thymis project git repository](../../external-projects/git-repository.md).
