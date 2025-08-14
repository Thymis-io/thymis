# Packaging software

In Thymis, you'll need to package your applications or dependencies for deployment on your devices. Thymis leverages Nix for reproducible builds and dependency management, making it easier to deploy consistent software across your device fleet.

## Packaging approaches

### Using existing packages
Start by checking if your software is already available in [Nixpkgs](https://search.nixos.org/packages). If it is, you can simply reference it in your module configurations without any additional packaging work.

### Custom packaging
When your software isn't available or requires customizations, you'll need to create a Nix expression for it. This ranges from simple use of the `Custom Module` to writing full-fledged derivations.

## Next steps

1. **[Set up Nix](packaging-software/setting-up-nix.md)** locally for development and testing
2. **Learn Nix basics** with our [Nix 101 guide](packaging-software/nix-101.md)
3. **Check language-specific guides**:
   - [Python](packaging-software/languages.md#python)
   - [Node.js](packaging-software/languages.md#nodejs)
   - [C/C++](packaging-software/languages.md#cc)

## Creating a module

Once packaged, wrap your software in a [Thymis Module](thymis-modules.md) to make it configurable through the Thymis UI:

```python
class MyAppModule(Module):
    display_name = "My Application"

    # Add settings here
    api_key = Setting(type="string", ...)

    def write_nix_settings(self, f, path, settings, priority, project):
        # Include your package and configure it
        f.write("environment.systemPackages = [inputs.my-app];")
```

## External resources

For advanced packaging scenarios:
- [Nix.dev tutorials](https://nix.dev/tutorials) - Comprehensive Nix packaging guides
- [NixOS Wiki](https://wiki.nixos.org/wiki/NixOS_Wiki) - Community knowledge base
- [Nixpkgs manual](https://nixos.org/manual/nixpkgs/stable/) - Official packaging documentation

## Deployment

After creating and testing your package:

1. Add your module to a device configuration or tag
2. Commit your changes
3. Build and deploy to your devices

See [Deploy an Update](../device-lifecycle/update.md) for detailed deployment instructions.
