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
    in
    rec {
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
      download-image = { thymis-config ? throw "thymis-config is required. Provide with --argstr" }:
        let
          thymis-config-parsed = builtins.fromJSON thymis-config;
        in
        (nixpkgs.lib.nixosSystem {
          modules = [
            nixosModules.thymis
            { system.stateVersion = "23.05"; }
          ];
          specialArgs = {
            inherit inputs;
            thymis-config = thymis-config-parsed;
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
        in
        {
          thymis-frontend = pkgs.callPackage ./frontend { };
          thymis-controller = pkgs.callPackage ./controller {
            poetry2nix = (
              (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
            );
          };
        }
      );
      nixosModules = {
        thymis = ./thymis-nixos-module.nix;
      } // nixpkgs.lib.mapAttrs'
        (name: value: {
          name = "thymis-device-${name}";
          value = value;
        })
        (import ./devices.nix { inherit inputs; lib = nixpkgs.lib; });
    };
}
