# Setting up Nix

In order to package software or create custom NixOS modules for Thymis, you will often want to run and test **Nix** locally.
Even though Thymis itself runs Nix for you on the Controller, having a Nix environment on your development machine is useful for:

- Packaging and testing applications before integrating them into Thymis.
- Learning the Nix language and build process interactively.
- Updating and debugging your software without pushing to Thymis first.

This guide walks you through installing and configuring Nix on the most common platforms.


## 1. Installing Nix

### Linux & macOS

The recommended way to install Nix is to use the **Determinate Systems installer** or the official installer.
If you are new to Nix, start with Determinate’s installer as it also configures flakes support by default.

**Option A — Determinate Installer** (recommended):

```bash
sh <(curl -L https://install.determinate.systems/nix)
```

**Option B — Official Nix Installer**:

```bash
sh <(curl -L https://nixos.org/nix/install)
```

Choose **multi-user installation** unless you have specific needs for single-user mode.


### Windows

On Windows, Nix must run inside a Linux environment such as [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).

1. Install WSL2 and a Linux distribution (Ubuntu is common).
2. Open a WSL terminal and follow the **Linux installation** steps above.

> Thymis modules that target Linux devices cannot be built natively on Windows without WSL or a VM.


## 2. Enabling Flakes and the New CLI

If you have installed Nix using the Determinate Systems installer, flakes and the new `nix` command are already enabled.
You can safely skip this step.
If you used the official installer, you need to enable these features manually.

Thymis projects use **Nix Flakes** for reproducible builds and input management.
After installing Nix, ensure that Flakes and the new `nix` command are enabled.

Create or edit `$HOME/.config/nix/nix.conf` (Linux/macOS) and add:

```
experimental-features = nix-command flakes
```

You can check your configuration:

```bash
nix show-config | grep experimental-features
```

Expected output should contain:

```
experimental-features = nix-command flakes
```


## 3. Testing Your Nix Installation

Verify that Nix works and flakes are enabled:

```bash
nix --version
nix flake --help
```

You can also try building a simple expression:

```bash
nix eval nixpkgs#hello
```

You should see:

```
«derivation /nix/store/...-hello-2.12.1.drv»
```

## 4. Next Steps

With Nix installed, you can:

- Work through [Nix 101](nix-101.md) to learn the basics of the language.
- Explore [Languages](languages.md) for packaging guides in Python, Node.js, C/C++.
- Start packaging your own application and integrate it into Thymis using [external repositories](../external-repositories.md) or the [Nix Language Module](../thymis-modules/nix-language-module.md).


## See also
- [NixOS official manual](https://nixos.org/manual/nix/stable/)
- [nix.dev tutorials](https://nix.dev)
- [Nixpkgs search](https://search.nixos.org/packages)
