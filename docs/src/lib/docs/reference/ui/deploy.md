# Deploy

In the main toolbar, you will find the **Deploy** button, which is central to pushing configurations and updates to your devices.

![Deploy Button](./deploy-button.png)

> **Terminology Tip:**
> In Thymis, **Update**, **Commit**, and **Deploy** are distinct steps:
>
> 1. **[Update](update.md)** (toolbar) — refreshes your project’s _external inputs_ (nixpkgs, modules, external repos). This does **not** immediately change devices.
> 2. **Commit** — saves project changes (including updated inputs) into the repository so they can be built/deployed.
> 3. **Deploy** — builds and sends the committed configuration to devices.
>    For instructions on applying new versions of software or configuration to already‑connected devices, see [Deploy an Update](../../device-lifecycle/update.md).

Clicking **Deploy** opens the Deploy Modal, which allows you to commit changes and deploy to selected devices or tags in a single workflow.

![Deploy Modal](./deploy-modal.png)

## The Deploy Modal

The Deploy Modal shows you the current state of your project and lets you commit and deploy in one unified process.

If you have uncommitted changes, the modal displays them with:

- A list of modified files
- A commit message field with a pre‑filled message you can edit
- Two options based on your changes:
  - **Commit & Deploy** — when there are uncommitted changes
  - **Deploy** — when your repo is clean (already committed)

## Selecting Targets

You can deploy to:

- **Specific Device Configurations** by selecting them in the list
- **Tags** — deploys to all configurations/devices associated with that tag

A preview shows the affected configurations/devices before you confirm.

## Deployment Process

Deploying can be done in different ways:

### Over‑the‑Air (OTA) Updates

- Incrementally transfers only changed parts of the system
- Atomic switch to new configuration after verification
- Automatic rollback if the device fails to reconnect

### Full Image Replacement

- Builds a complete disk image for manual installation
- Useful for air‑gapped or recovery cases

## Three‑Phase Deployment

1. **Build** — unique device configuration → system closure
2. **Transfer** — send only new/changed paths to the device
3. **Switch** — atomically activate the new configuration

## Reliability and Recovery

Thymis automatically rolls back if:

- The device fails during the switch phase and can’t reconnect
- The connection to the controller fails before activation completes

Previous configurations remain available as rollback points.

## Task Management

Deployment creates two levels of tasks:

- **Deployment Task** — overall operation
- **Per‑Device Tasks** — track status for each target device

Monitor with the **Tasks** view.

![Deployment Tasks](./deployment-tasks.png)

## Current Limitations

Thymis has some limitations in deployment error handling:

- **Partial failures**: If a systemd service fails to start, the deployment may be marked as failed even though the system has already switched. You can verify this by:
  1. Checking the commit hash in the **Devices** table—it shows which configuration is running
  2. Using the **Terminal** to inspect device logs
  3. reviewing the deployment task logs

This limitation will be addressed in future UI improvements for better deployment status visibility.


## Best Practices

**Before Deployment:**

1. Review target devices carefully.
2. Use **Build** to validate large or complex changes.
3. Test on one device before deploying fleet‑wide.

**After Deployment:**

- Check **Tasks** for failures.
- Verify device connectivity in the **Devices** view.
- Use the **Terminal** to confirm services are running.

## Related Pages

- [Build](build.md) — verify configurations before deploying
- [Update](update.md) — fetch new input versions
- [Deploy an Update](../../device-lifecycle/update.md) — push updated packages/configurations to devices
- [Tasks](tasks.md)
- [Troubleshooting](../../device-lifecycle/troubleshooting.md)
