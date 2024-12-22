{
  description = "Thymis";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-24.11";
    home-manager.url = "github:nix-community/home-manager/release-24.11";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
    nixos-generators.url = "github:nix-community/nixos-generators";
    nixos-generators.inputs.nixpkgs.follows = "nixpkgs";
    nixos-hardware.url = "github:NixOS/nixos-hardware";
    raspberry-pi-nix.url = "github:nix-community/raspberry-pi-nix";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs = inputss@{ self, nixpkgs, home-manager, poetry2nix, flake-utils, ... }:
    let
      inputs = inputss // {
        thymis = self;
      };
      eachSystem = nixpkgs.lib.genAttrs (import ./flake.systems.nix);
      nixosModules = {
        thymis-device = ./thymis-device-nixos-module.nix;
        thymis-controller = ./thymis-controller-nixos-module.nix;
      } // (nixpkgs.lib.mapAttrs'
        (name: value: {
          name = "thymis-device-${name}";
          value = value;
        })
        (import ./devices.nix { inherit inputs; lib = nixpkgs.lib; })
      ) // (nixpkgs.lib.mapAttrs'
        (name: value: {
          name = "thymis-image-${name}";
          value = value;
        })
        (import ./image-formats.nix { inherit inputs; lib = nixpkgs.lib; })
      );

      thymis-controller-pi-3-sd-image = (nixpkgs.lib.nixosSystem {
        modules = [
          nixosModules.thymis-device
          nixosModules."thymis-device-raspberry-pi-3"
          nixosModules."thymis-image-sd-card-image"
          nixosModules.thymis-controller
          {
            services.thymis-controller.enable = true;
            system.stateVersion = "24.11";
          }
        ];
        specialArgs = {
          inherit inputs;
        };
      }).config.system.build.thymis-image;

      thymis-controller-pi-4-sd-image = (nixpkgs.lib.nixosSystem {
        modules = [
          nixosModules.thymis-device
          nixosModules."thymis-device-raspberry-pi-4"
          nixosModules."thymis-image-sd-card-image"
          nixosModules.thymis-controller
          {
            services.thymis-controller.enable = true;
            system.stateVersion = "24.11";
          }
        ];
        specialArgs = {
          inherit inputs;
        };
      }).config.system.build.thymis-image;

      thymis-controller-pi-5-sd-image = (nixpkgs.lib.nixosSystem {
        modules = [
          nixosModules.thymis-device
          nixosModules."thymis-device-raspberry-pi-5"
          nixosModules."thymis-image-sd-card-image"
          nixosModules.thymis-controller
          {
            services.thymis-controller.enable = true;
            system.stateVersion = "24.11";
          }
        ];
        specialArgs = {
          inherit inputs;
        };
      }).config.system.build.thymis-image;

      thymis-controller-generic-x86_64-image = (nixpkgs.lib.nixosSystem {
        modules = [
          nixosModules.thymis-device
          nixosModules."thymis-device-generic-x86_64"
          nixosModules."thymis-image-qcow"
          nixosModules.thymis-controller
          {
            services.thymis-controller.enable = true;
            system.stateVersion = "24.11";
          }
        ];
        specialArgs = {
          inherit inputs;
        };
      }).config.system.build.thymis-image;

      removeRecurseForDerivations = nixpkgs.lib.filterAttrsRecursive (k: v: k != "recurseForDerivations");
    in
    {
      inputs = inputs;
      formatter = eachSystem (system: nixpkgs.legacyPackages.${system}.nixpkgs-fmt);
      devShells = eachSystem (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.poetry
              pkgs.python312
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
            '';
          };
        });


      packages = eachSystem (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          thymis-frontend = pkgs.callPackage ./frontend { };
          thymis-controller = pkgs.callPackage ./controller {
            poetry2nix = (
              (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
            );
            thymis-frontend = thymis-frontend;
          };
          thymis-agent = pkgs.callPackage ./agent {
            poetry2nix = (
              (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
            );
          };
        in
        {
          thymis-controller = thymis-controller;
          thymis-controller-container = import ./docker.nix { inherit pkgs thymis-controller; };
          thymis-agent = thymis-agent;
        }
      );
      nixosModules = nixosModules;
      thymis-controller-pi-3-sd-image = thymis-controller-pi-3-sd-image;
      thymis-controller-pi-4-sd-image = thymis-controller-pi-4-sd-image;
      thymis-controller-pi-5-sd-image = thymis-controller-pi-5-sd-image;
      thymis-controller-generic-x86_64-image = thymis-controller-generic-x86_64-image;
      hydraJobs = {
        thymis-controller-pi-3-sd-image = thymis-controller-pi-3-sd-image;
        thymis-controller-pi-4-sd-image = thymis-controller-pi-4-sd-image;
        thymis-controller-pi-5-sd-image = thymis-controller-pi-5-sd-image;
        thymis-controller-generic-x86_64-image = thymis-controller-generic-x86_64-image;
      };
    };
}
