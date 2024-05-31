{
  description = "Thymis";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-23.11";
    home-manager.url = "github:nix-community/home-manager/release-23.11";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
    nixos-generators.url = "github:nix-community/nixos-generators";
    nixos-generators.inputs.nixpkgs.follows = "nixpkgs";
    nixos-hardware.url = "github:NixOS/nixos-hardware";
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
        thymis = ./thymis-nixos-module.nix;
      } // nixpkgs.lib.mapAttrs'
        (name: value: {
          name = "thymis-device-${name}";
          value = value;
        })
        (import ./devices.nix { inherit inputs; lib = nixpkgs.lib; });
      download-image = { thymis-config ? throw "thymis-config is required. Provide with --argstr" }:
        let
          thymis-config-parsed = builtins.fromJSON thymis-config;
        in
        (nixpkgs.lib.nixosSystem {
          modules = [
            nixosModules.thymis
            nixosModules."thymis-device-${thymis-config-parsed.device-type}"
            {
              thymis.config = thymis-config-parsed;
              # thymis.controller.enable = true;
              system.stateVersion = "23.11";
            }
          ];
          specialArgs = {
            inherit inputs;
          };
        });
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
              pkgs.nodejs
              pkgs.pre-commit
            ];
          };
        });

      all-download-images =
        let
          devices = import ./devices.nix { lib = nixpkgs.lib; };
          device-formats = builtins.mapAttrs
            (name: device:
              let
                thymis-config = {
                  device-type = name;
                  password = "";
                };
              in
              (download-image { thymis-config = builtins.toJSON thymis-config; }).config.formats // {
                recurseForDerivations = true;
              })
            devices;

        in
        device-formats // {
          recurseForDerivations = true;
        };
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
        in
        {
          thymis-frontend = thymis-frontend;
          thymis-controller = thymis-controller;
          thymis-controller-container = import ./docker.nix { inherit pkgs thymis-controller; };
          thymis-frontend-container = pkgs.dockerTools.buildLayeredImage {
            name = "thymis-frontend";
            config = {
              Cmd = [ "${thymis-frontend}/bin/thymis-controller" ];
            };
          };
        }
      );
      nixosModules = nixosModules;
    };
}
