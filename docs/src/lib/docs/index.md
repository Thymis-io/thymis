# Introduction

Thymis is an open‑source platform for managing IoT devices using [NixOS](https://nixos.org).
It lets you provision, configure, update, and monitor fleets of devices.
With the reliability and reproducibility that comes from a declarative configuration.


## Who This Is For

- IoT solution vendors deploying and maintaining large device fleets.
- Developers creating custom applications for embedded Linux devices.
- Ops/IT teams needing reproducible, version‑controlled device configurations.

If you need a secure, infrastructure‑as‑code‑style way to manage devices, from Raspberry Pi kiosks to generic x86 gateways, Thymis provides the tooling.

## What You’ll Find in This Documentation

- Step‑by‑step setup for [Thymis Cloud](setting-up-thymis/thymis-cloud.md), [NixOS](setting-up-thymis/nixOS.md), or [Docker](setting-up-thymis/oci-container.md).

- Guides for [provisioning devices](device-lifecycle/getting-started.md), sharing settings with [Tags](device-lifecycle/tags.md), enabling [Kiosk mode with VNC](device-lifecycle/kiosk.md), [performing updates](device-lifecycle/update.md), [testing in VMs](device-lifecycle/vms.md), and [troubleshooting](device-lifecycle/troubleshooting.md).

- How to integrate external repositories, use and create a [Thymis Modules](external-projects/thymis-modules.md), package software with Nix, and tailor devices to your applications.

- Comprehensive background on [concepts](reference/concepts.md) (devices, deployments, configurations, tags, modules, secrets, artifacts), [administration](reference/administration.md), UI field reference, and [supported hardware](reference/supported-devices.md).

## Community & Support

Thymis is developed by the [Udysseus GmbH](https://udysseus.com) and released under [AGPL‑3.0](https://github.com/Thymis-io/thymis/blob/master/LICENSE).

For updates, source code, and community discussions:

- [GitHub: Thymis repositories](https://github.com/thymis-io)
- [NixOS Discourse: Thymis announcement](https://discourse.nixos.org/t/thymis-web-based-dashboard-and-device-provisioning-for-nixos/)

## Ready to begin?

Start with [Setting Up Thymis](setting-up-thymis.md) or use the sidebar to explore guides, module references, and lifecycle workflows for your devices.
