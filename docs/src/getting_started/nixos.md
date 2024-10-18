# Thymis NixOS module

In order to deploy the Thymis controller, you can use the Thymis NixOS module.

## Installation (using flakes)

1. Add the Thymis repository to your `flake.nix`:

```nix
{
  inputs.thymis.url = "github:Thymis-io/thymis/v0.1";
}
```

2. Add the Thymis module to your NixOS configuration:

For example:

Add flake `inputs` to NixOS Module `specialArgs` in call to `nixosSystem` (probably in `flake.nix`).

Add NixOS module `thymis.nixosModules.thymis-controller` to the configuration (for example in `modules` parameter of `nixosSystem`).

```nix
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
```

3. Configure the Thymis controller in your NixOS configuration (for example in `configuration.nix`):

```nix
{
  services.thymis-controller = {
    enable = true;
    system-binfmt-aarch64-enable = true; # enables emulation of aarch64 binaries, default is true on x86_64, needed for building aarch64 images on x86_64
    system-binfmt-x86_64-enable = false; # enables emulation of x86_64 binaries, default is false
    repo-path = "/var/lib/thymis/repository"; # directory where the controller will store the repository holding the project
    database-url = "sqlite:////var/lib/thymis/thymis.sqlite"; # URL of the database
    base-url = "https://my-thymis-controller/"; # base URL of the controller, how it will be accessed from the outside
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
```

Don't forget to replace `MY_SYSTEM_HERE` with the name of your system and `YOUR MODULES HERE` with the modules you want to include in your system, and to replace `my-thymis-controller` with the actual domain name of your controller.

Build and deploy your system:

```sh
sudo nixos-rebuild switch --flake .#MY_SYSTEM_HERE
```

4. Access the Thymis controller at the base URL you configured (e.g. `https://my-thymis-controller/`).

The password for basic authentication is stored in the file `/var/lib/thymis/auth-basic-password`. If not present, it will be generated automatically and filled with a random password. Use this password to log in to the controller, together with the username set during configuration.
