# NixOS


<!-- In order to deploy the Thymis controller, you can use the Thymis NixOS module.
Installation (using flakes)

    Add the Thymis repository to your flake.nix:

{
  inputs.thymis.url = "github:Thymis-io/thymis/v0.6";
}

    Add the Thymis module to your NixOS configuration:

For example:

Add flake inputs to NixOS Module specialArgs in call to nixosSystem (probably in flake.nix).

Add NixOS module thymis.nixosModules.thymis-controller to the configuration (for example in modules parameter of nixosSystem).

{
    outputs = inputs@{ self, nixpkgs, ... }:{
        nixosConfigurations.MY_SYSTEM_HERE = nixpkgs.lib.nixosSystem {
            system = "x86_64-linux";
            specialArgs = {
                inherit inputs;
            };
            modules = [
                YOUR MODULES HERE
                ./configuration.nix
                inputs.thymis.nixosModules.thymis-controller
            ];
        };
    };
}

    Configure the Thymis controller in your NixOS configuration (for example in configuration.nix):

{
  services.thymis-controller = {
    enable = true;
    system-binfmt-aarch64-enable = true; # enables emulation of aarch64 binaries, default is true on x86_64, needed for building aarch64 images on x86_64
    system-binfmt-x86_64-enable = false; # enables emulation of x86_64 binaries, default is false
    recommended-nix-gc-settings-enable = true; # enables recommended Nix garbage collection settings, default is true
    repo-path = "/var/lib/thymis/repository"; # directory where the controller will store the repository holding the project
    database-url = "sqlite:////var/lib/thymis/thymis.sqlite"; # URL of the database
    base-url = "https://my-thymis-controller/"; # base URL of the controller, how it will be accessed from the outside
    agent-access-url = "https://my-thymis-controller/"; # URL of the controller to be used by the agents
    auth-basic = true; # whether to enable authentication using a basic username/password
    auth-basic-username = "admin"; # username for basic authentication
    auth-basic-password-file = "/var/lib/thymis/auth-basic-password"; # file containing the password for basic authentication
    # content will be automatically generated if it does not exist
    listen-host = "127.0.0.1"; # host on which the controller listens for incoming connections
    listen-port = 8000; # port on which the controller listens for incoming connections
    nginx-vhost-enable = true; # whether to enable the Nginx virtual host
    nginx-vhost-name = "thymis"; # name of the Nginx virtual host
  };
  # Configure the Nginx virtual host
  services.nginx = {
    enable = true;
    virtualHosts."thymis" = {
      serverName = "my-thymis-controller";
      enableACME = true;
      forceSSL = true;
    };
  };
}

Don't forget to replace MY_SYSTEM_HERE with the name of your system and YOUR MODULES HERE with the modules you want to include in your system, and to replace my-thymis-controller with the actual domain name of your controller.

Build and deploy your system:

sudo nixos-rebuild switch --flake .#MY_SYSTEM_HERE

    Access the Thymis controller at the base URL you configured (e.g. https://my-thymis-controller/).

The password for basic authentication is stored in the file /var/lib/thymis/auth-basic-password. If not present, it will be generated automatically and filled with a random password. Use this password to log in to the controller, together with the username set during configuration. -->


Thymis can be set up on NixOS using the Thymis NixOS module. This module provides a simple and reproducible way to deploy the Thymis Controller and its dependencies.

## Installation (using flakes)

Using Nix Flakes, you can set up Thymis on NixOS by following these steps:

### 1. Add the Thymis repository to your `flake.nix`

```nix
{
  inputs.thymis.url = "github:Thymis-io/thymis/v0.6";
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
             YOUR_MODULES_HERE
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
    repo-path = "/var/lib/thymis/repository"; # Directory for the project repository
    database-url = "sqlite:////var/lib/thymis/thymis.sqlite"; # Database URL
    base-url = "https://my-thymis-controller/"; # Base URL of the controller
    agent-access-url = "https://my-thymis-controller/"; # URL for agents to access the controller
    auth-basic = true; # Enable basic authentication
    auth-basic-username = "admin"; # Username for basic authentication
    auth-basic-password-file = "/var/lib/thymis/auth-basic-password"; # File containing the password for basic authentication
    listen-host = "127.0.0.1"; # host on which the controller listens for incoming connections
    listen-port = 8000; # port on which the controller listens for incoming connections
    nginx-vhost-enable = true; # whether to enable the Nginx virtual host
    nginx-vhost-name = "thymis"; # name of the Nginx virtual host
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

Don't forget to replace `MY_SYSTEM_HERE` with the name of your system and `YOUR_MODULES_HERE` with the modules you want to include in your system, and to replace `my-thymis-controller` with the actual domain name of your controller.

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
- Update your thymis controller regularly to benefit from the latest features and security updates.

See also [Administration](../../reference/administration.md) for more information on how to manage Thymis in a self-hosted environment.
