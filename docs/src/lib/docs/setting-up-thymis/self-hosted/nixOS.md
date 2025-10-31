# NixOS

Thymis can be set up on NixOS using the Thymis NixOS module. This module provides a simple and reproducible way to deploy the Thymis Controller and its dependencies.

## Installation (using flakes)

Using Nix Flakes, you can set up Thymis on NixOS by following these steps:

### 1. Add the Thymis repository to your `flake.nix`

```nix
{
  inputs.thymis.url = "github:Thymis-io/thymis/v0.7";
}
```

### 2. Add the Thymis module to your NixOS configuration

For example, in your `flake.nix`, you can define your NixOS system like this:

```nix
{
  outputs = inputs@{ self, nixpkgs, ... }:
     {
        nixosConfigurations.MY_SYSTEM_HERE = nixpkgs.lib.nixosSystem {
          system = "x86_64-linux";
          specialArgs = { inherit inputs; };
          modules = [
             # your other modules
             ./configuration.nix
             inputs.thymis.nixosModules.thymis-controller
          ];
        };
     };
}
```

### 3. Configure the Thymis controller in your NixOS configuration

In your `configuration.nix`, you can configure the Thymis controller like this:

```nix
{
  services.thymis-controller = {
    enable = true;
    system-binfmt-aarch64-enable = true; # Enables emulation of aarch64 binaries
    system-binfmt-x86_64-enable = false; # Enables emulation of x86_64 binaries
    recommended-nix-gc-settings-enable = true; # Enables recommended Nix garbage collection settings
    project-path = "/var/lib/thymis"; # Directory for the project
    base-url = "https://my-thymis-controller/"; # Base URL of the controller
    agent-access-url = "https://my-thymis-controller/"; # URL for agents to access the controller
    auth-basic = true; # Enable basic authentication
    auth-basic-username = "admin"; # Username for basic authentication
    auth-basic-password-file = "/var/lib/thymis/auth-basic-password"; # File containing the password for basic authentication
    listen-host = "127.0.0.1"; # Host on which the controller listens for incoming connections
    listen-port = 8000; # Port on which the controller listens for incoming connections
    nginx-vhost-enable = true; # Whether to enable the Nginx virtual host
    nginx-vhost-name = "thymis"; # Name of the Nginx virtual host
  };
  # Configure the Nginx virtual host
  services.nginx = {
    enable = true;
    virtualHosts."thymis" = {
      serverName = "my-thymis-controller";
      enableACME = true; # Enable ACME for automatic SSL certificate management
      forceSSL = true; # Force SSL for the virtual host
    };
  };
}
```

Don't forget to replace `MY_SYSTEM_HERE` with the name of your system and `./configuration.nix`/other modules with the modules you want to include in your system, and to replace `my-thymis-controller` with the actual domain name of your controller.

### 4. Build and deploy your system

After configuring your NixOS system, you can build and deploy it using the following command:

```bash
sudo nixos-rebuild switch --flake .#MY_SYSTEM_HERE
```

Change `MY_SYSTEM_HERE` to the name of your system as defined in your `flake.nix`, and ensure you are in the directory containing your `flake.nix`.

### 5. Access the Thymis controller

You can access the Thymis controller at the base URL you configured (e.g., `https://my-thymis-controller/`).

The password for basic authentication is stored in the file `/var/lib/thymis/auth-basic-password`. If this file is not present, it will be generated automatically with a random password. Use this password to log in to the controller, together with the username set during configuration.

## Additional Notes

- Thymis requires sufficient storage space for device images and artifacts, so ensure that your NixOS system has enough disk space allocated.
- Update your Thymis controller regularly to benefit from the latest features and security updates.

See also [Administration](../../reference/administration.md) for more information on how to manage Thymis in a self-hosted environment.
