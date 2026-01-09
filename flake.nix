{
  description = "Thymis";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    home-manager.url = "github:nix-community/home-manager/release-25.11";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
    nixos-generators.url = "github:nix-community/nixos-generators";
    nixos-generators.inputs.nixpkgs.follows = "nixpkgs";
    nixos-hardware.url = "github:NixOS/nixos-hardware";
    raspberry-pi-nix.url = "github:nix-community/raspberry-pi-nix";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    disko.url = "github:nix-community/disko/master";
    disko.inputs.nixpkgs.follows = "nixpkgs";
  };

  nixConfig = {
    extra-substituters = [
      "https://cache.thymis.io"
    ];
    extra-trusted-public-keys = [
      "cache.thymis.io-1:pEeKkNXiK17TLKls0KM8cEp0NGy08gc5chAmCyuQo8M="
    ];
  };

  outputs = inputss@{ self, nixpkgs, home-manager, flake-utils, ... }:
    let
      inputs = inputss // {
        thymis = self;
      };
      forAllSystems = nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" ];
      nixosModules = {
        thymis-device = ./nix/thymis-device-nixos-module.nix;
        thymis-controller = {
          imports = [
            ./nix/thymis-controller-nixos-module.nix
          ];
          nixpkgs.overlays = [
            (final: prev: {
              thymis-controller = self.packages.${final.stdenv.system}.thymis-controller;
            })
          ];
        };
      } // (nixpkgs.lib.mapAttrs'
        (name: value: {
          name = "thymis-device-${name}";
          value = value;
        })
        (import ./nix/devices.nix { inherit inputs; lib = nixpkgs.lib; })
      ) // (nixpkgs.lib.mapAttrs'
        (name: value: {
          name = "thymis-image-${name}";
          value = value;
        })
        (import ./nix/image-formats.nix { inherit inputs; lib = nixpkgs.lib; })
      );

      activate-thymis-controller-module = {
        services.thymis-controller.enable = true;
        services.thymis-controller.base-url = "https://thymis.example.com";
        services.thymis-controller.agent-access-url = "https://thymis.example.com";
        system.stateVersion = "25.11";
      };

      thymis-controller-pi-3-sd-image = (nixpkgs.lib.nixosSystem {
        modules = [
          nixosModules.thymis-device
          nixosModules."thymis-device-raspberry-pi-3"
          nixosModules."thymis-image-sd-card-image"
          nixosModules.thymis-controller
          activate-thymis-controller-module
        ];
        specialArgs = {
          inherit inputs;
        };
      }).config.system.build.thymis-image-with-secrets-builder-aarch64;

      thymis-controller-pi-4-sd-image = (nixpkgs.lib.nixosSystem {
        modules = [
          nixosModules.thymis-device
          nixosModules."thymis-device-raspberry-pi-4"
          nixosModules."thymis-image-sd-card-image"
          nixosModules.thymis-controller
          activate-thymis-controller-module
        ];
        specialArgs = {
          inherit inputs;
        };
      }).config.system.build.thymis-image-with-secrets-builder-aarch64;

      thymis-controller-pi-5-sd-image = (nixpkgs.lib.nixosSystem {
        modules = [
          nixosModules.thymis-device
          nixosModules."thymis-device-raspberry-pi-5"
          nixosModules."thymis-image-sd-card-image"
          nixosModules.thymis-controller
          activate-thymis-controller-module
        ];
        specialArgs = {
          inherit inputs;
        };
      }).config.system.build.thymis-image-with-secrets-builder-aarch64;

      thymis-controller-generic-x86_64-image = (nixpkgs.lib.nixosSystem {
        modules = [
          nixosModules.thymis-device
          nixosModules."thymis-device-generic-x86_64"
          nixosModules."thymis-image-qcow"
          nixosModules.thymis-controller
          activate-thymis-controller-module
        ];
        specialArgs = {
          inherit inputs;
        };
      }).config.system.build.thymis-image-with-secrets-builder-x86_64;

    in
    {
      inputs = inputs;
      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixpkgs-fmt);
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.uv
              pkgs.python313
              pkgs.nodejs_22
              pkgs.pre-commit
              pkgs.playwright-driver.browsers
              pkgs.mdbook
              pkgs.nixpkgs-fmt
            ];
            shellHook = ''
              export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
              export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
              export THYMIS_DEV_SHELL=true
              export THYMIS_FLAKE_ROOT=$(git rev-parse --show-toplevel)
              alias run-dev="(cd $THYMIS_FLAKE_ROOT/controller && UVICORN_PORT=8080 uv run uvicorn thymis_controller.main:app --reload --host 0.0.0.0 --port 8080)"
            '';
          };
          ci = pkgs.mkShell {
            packages = [
              pkgs.uv
              pkgs.python313
              pkgs.nodejs_22
              pkgs.nixpkgs-fmt
              pkgs.pre-commit
              pkgs.which
              pkgs.curl
              pkgs.rustup
            ];
          };
          forNpmTesting = pkgs.mkShell {
            packages = [
              pkgs.playwright-driver.browsers
              pkgs.nodejs_22
              pkgs.uv
              pkgs.python313
              pkgs.nixpkgs-fmt
              pkgs.git
              pkgs.openssh
            ];
            shellHook = ''
              export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
              export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
            '';
            PLAYWRIGHT_BROWSERS_PATH = pkgs.playwright-driver.browsers;
            PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = "true";
          };
        });
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          thymis-frontend = pkgs.callPackage ./frontend {
            git-rev = inputs.self.rev or inputs.self.dirtyRev or null;
          };
          thymis-controller = pkgs.callPackage ./controller {
            inherit (inputs)
              pyproject-build-systems
              pyproject-nix
              uv2nix;
            thymis-frontend = thymis-frontend;
          };
          thymis-agent = pkgs.callPackage ./agent {
            inherit (inputs)
              pyproject-build-systems
              pyproject-nix
              uv2nix;
          };
        in
        {
          thymis-frontend = thymis-frontend;
          thymis-controller = thymis-controller;
          thymis-agent = thymis-agent;
          thymis-controller-container = import ./nix/docker.nix { inherit pkgs thymis-controller; };
        }
      );
      nixosModules = nixosModules;
      thymis-controller-pi-3-sd-image = thymis-controller-pi-3-sd-image;
      thymis-controller-pi-4-sd-image = thymis-controller-pi-4-sd-image;
      thymis-controller-pi-5-sd-image = thymis-controller-pi-5-sd-image;
      thymis-controller-generic-x86_64-image = thymis-controller-generic-x86_64-image;
    };
}
