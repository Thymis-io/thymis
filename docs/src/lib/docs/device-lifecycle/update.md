# Deploy an Update

In Thymis there are **two different kinds of “update”**:

1. **Toolbar “Update” button** — updates your *project’s external inputs* (Nix Flake dependencies such as nixpkgs, Thymis modules, and external repositories).
   It does **not** directly update the software running on devices — it just refreshes the versions available to your project. See [Update in the UI Reference](../reference/ui/update.md).
2. **Deploying updated configurations/packages to devices** — what this page describes: pushing newer versions of software and configuration changes to devices that are already provisioned.


If an OTA (over‑the‑air) deployment fails or a device cannot reconnect to the Thymis Controller, the previous configuration will be rolled back automatically.


## Updating Packages in a Device Configuration

1. Click the **Update** button **inside the device configuration view** (not the toolbar one) to bump all packages in that configuration to the latest versions available from your current inputs.

   This creates an **Update Nix Flake** task.

2. Wait until this task completes before proceeding.

![Update Config Packages](./Color-scheme-light-deploy-update-1-linux.png)


## Deploy the Changes

1. Once the update task has completed, click the **Deploy** button.

   ![Deploy Button](./Color-scheme-light-deploy-update-2-linux.png)

2. In the Deploy modal:
   - Select the **Tags** and/or **Configs** you want to deploy.
   - Confirm the target devices in the preview list.
   - Click **Deploy**.

![Deploy Modal](./Color-scheme-light-deploy-update-3-linux.png)

Thymis will:
- Build the updated system closure for each target device.
- Transfer only changes (incremental OTA update).
- Atomically switch devices to the new configuration.

If the deployment fails, see [Troubleshooting](troubleshooting.md).


## Best Practices

- Always distinguish between:
  - **Toolbar “Update”** — refresh external input versions.
  - **Config‑level “Update”** — bump packages in a specific device configuration.
- Use **Build** before Deploy to validate changes.
- When doing large version jumps, test on a single device before rolling out fleet‑wide.


## See also
- [UI Reference — Update](../reference/ui/update.md) (Flake Inputs)
- [Build](../reference/ui/build.md)
- [Deploy](../reference/ui/deploy.md)
- [Troubleshooting](troubleshooting.md)
