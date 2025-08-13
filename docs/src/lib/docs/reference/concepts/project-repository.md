# Project repository
<!-- .
├── flake.lock
├── flake.nix
├── hosts
│   ├── aaa
│   │   ├── thymis_controller.modules.kiosk.Kiosk.nix
│   │   └── thymis_controller.modules.thymis.ThymisDevice.nix
│   ├── asdasd
│   │   ├── thymis_controller.modules.kiosk.Kiosk.nix
│   │   ├── thymis_controller.modules.thymis.ThymisDevice.nix
│   │   └── thymis_controller.modules.whatever.WhateverModule.nix
│   ├── demo
│   │   ├── thymis_controller.modules.kiosk.Kiosk.nix
│   │   └── thymis_controller.modules.thymis.ThymisDevice.nix
│   ├── new-device-for-documentation
│   │   └── thymis_controller.modules.thymis.ThymisDevice.nix
│   └── testpi
│       └── thymis_controller.modules.thymis.ThymisDevice.nix
├── modules
├── state.json
└── tags
    ├── fdghdfghsdfsvd-as-as-as-as-das-da-sa
    ├── office-wifi
    │   └── thymis_controller.modules.thymis.ThymisDevice.nix
    ├── ssh-keys
    │   └── thymis_controller.modules.thymis.ThymisDevice.nix
    └── this-is-my-new-tag-name
        └── thymis_controller.modules.kiosk.Kiosk.nix -->

In Thymis, your project is backed by a Git repository that contains all the necessary files to manage your devices, configurations, and modules. This repository is referred to as the **Project Repository**.
It is automatically created when you set up your Thymis Controller and is used to store the state of your devices, configurations, and modules.

## Structure of the Project Repository

The project repository is structured as follows:

```
/var/lib/thymis/repository/
├── state.json # JSON file containing the state of the project, including devices, configurations, and modules
├── flake.nix # Generated from state.json: Nix flake file, entry-point for your nix expressions, contains the inputs and outputs of your project
├── flake.lock # Nix flake lock file, contains the state of the inputs
├── hosts/ # Directory containing device configurations, one sub-directory per device
│   ├── <device-name>/ # Directory for a specific device, contains the device configuration
│   │   ├── thymis_controller.modules.thymis.ThymisDevice.nix # Device configuration file, contains the Thymis module for the device
│   │   └── <other-module>.nix # Other Thymis modules for the device, if any
└── tags/ # Directory containing tags, one sub-directory per tag
    └── <tag-name>/ # Directory for a specific tag, contains the tag configuration
        └── <module-name>.nix # Thymis module for the tag, contains the configuration for the tag
```

The `state.json` file contains the state of the project, including devices, configurations, and modules.
It is generated from the Thymis UI and is used to keep track of the devices, configurations, and modules in your project.
When you add or remove devices, configurations, or modules in the Thymis UI, the `state.json` file is updated accordingly.

The `flake.nix` file is generated from the `state.json` file and contains the Nix expressions for your project.
Every time you make changes to the project in the Thymis UI, the `flake.nix` file is updated to reflect those changes.

The `flake.lock` file is a Nix flake lock file that contains the state of the inputs for your project.
It is generated from the `flake.nix` file and is used to ensure that the inputs for your project are consistent across different deployments.
This file is updated using the [**Update**](../ui/update.md) button in the Thymis UI, which fetches the latest changes from the inputs and updates the `flake.lock` file accordingly.

The `hosts/` directory contains the device configurations, with one sub-directory per device.
Each sub-directory contains the device configuration file, which is a Thymis module that defines the configuration for the device.
The device configuration file is named `thymis_controller.modules.thymis.ThymisDevice.nix` and contains the Thymis module for the device.
You can also have other Thymis modules in the device sub-directory, which can be used to define additional configurations for the device.

The `tags/` directory contains the tags, with one sub-directory per tag.
Each sub-directory contains the tag configuration file, which is a Thymis module that defines the configuration for the tag.
The tag configuration file is named `<module-name>.nix` and contains the Thymis module for the tag.
This allows you to group devices and configurations together and apply the same configurations to multiple devices using tags.

## Accessing the Project Repository

You can access the project repository of your Thymis Controller.
This is described in the [Accessing the Thymis project git repository](../../external-projects/git-repository.md) documentation.
