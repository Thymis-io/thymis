# Using the Nix language module

The Nix language module allows you to write Nix expressions to configure devices directly in Thymis. This is particularly useful when you are testing options or want to quickly prototype a configuration without creating a full Thymis module.

Start by adding a "Custom Module" to your device or tag. You can do this by clicking the **Plus** button in the **Modules** section of the device or tag configuration page.

![Add Custom Module](./add-custom-module.png)

Once added, select the **Custom Module** from the list of loaded modules. In the configuration section, you will find a text area where you can write your Nix expressions.

![Custom Module Configuration](./custom-module-configuration.png)

The configuration you write here will be placed in the body of a NixOS module, which is then applied to the device when it is deployed.

The exact template used is:

```nix
{ pkgs, lib, inputs, config, ... }:
{
  # Your NixOS module configuration goes here
}
```

For example, to install vim on the device:

```nix
environment.systemPackages = with pkgs; [ vim ];
```

Like this:

![Custom Module Example](./custom-module-example.png)

For guidance on how to write NixOS modules, see [Nix 101 - Configuring Devices with Nix](../../external-projects/packaging-software/nix-101.md#configuring-devices-with-nix).

You can consult resources online, such as the [NixOS wiki](https://wiki.nixos.org/wiki/NixOS_modules) or the [NixOS manual](https://nixos.org/manual/nixos/stable/) to learn more about how to write NixOS modules and what options are available.

We recommend using the [Nixpkgs search](https://search.nixos.org/packages) to find available packages and the [NixOS options search](https://search.nixos.org/options) to find available configuration options.

Tip: Want to run Python code on your devices? See [Using the Python language module (coming soon)](python-language-module.md) for a workaround using `pkgs.writers.writePython3`.
