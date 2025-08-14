# Introduction

Welcome to the **Thymis** documentation.

Thymis is an open‑source platform for managing IoT devices using the declarative power of [NixOS](https://nixos.org).
It enables you to provision, configure, update, and monitor fleets of devices with full reproducibility and reliability — whether they’re in the cloud, on‑premises, or behind NAT.

## Who This Is For

- IoT solution vendors deploying and maintaining large device fleets.
- Developers creating custom applications for embedded Linux devices.
- Ops/IT teams needing reproducible, version‑controlled device configurations.

If you need a secure, infrastructure‑as‑code‑style way to manage devices — from Raspberry Pi kiosks to generic x86 gateways — Thymis provides the tooling.

## What You’ll Find in This Documentation

- **Getting Started**
  Step‑by‑step setup for [Thymis Cloud](setting-up-thymis/thymis-cloud.md) or [self‑hosting](setting-up-thymis/self-hosted.md), including [NixOS deployments](setting-up-thymis/self-hosted/nixOS.md) and planned [OCI‑container support](setting-up-thymis/self-hosted/oci-container.md).

- **Device Lifecycle**
  Guides for [provisioning devices](device-lifecycle/getting-started.md), sharing settings with [Tags](device-lifecycle/tags.md), enabling [Kiosk mode with VNC](device-lifecycle/kiosk.md), performing updates, testing in VMs, and troubleshooting.

- **Projects & Modules**
  How to integrate external repositories, use and create [Thymis Modules](external-projects/thymis-modules.md), package software with Nix, and tailor devices to your applications.

- **Reference**
  Comprehensive background on [concepts](reference/concepts.md) (devices, deployments, configurations, tags, modules, secrets, artifacts), [administration](reference/administration.md), UI field reference, and [supported hardware](reference/supported-devices.md).

## Community & Support

Thymis is developed by **Udysseus GmbH** and released under [AGPL‑3.0](https://www.gnu.org/licenses/agpl-3.0.html).

For updates, source code, and community discussions:

- [GitHub — Thymis repositories](https://github.com/thymis-io)
- [NixOS Discourse: Thymis announcement](https://discourse.nixos.org/t/thymis-web-based-dashboard-and-device-provisioning-for-nixos/)

## Ready to begin?

Start with [Setting Up Thymis](setting-up-thymis.md) or use the sidebar to explore guides, module references, and lifecycle workflows for your devices.
