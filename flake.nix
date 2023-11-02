{
  description = "Thymis";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-23.05";
    home-manager.url = "github:nix-community/home-manager/release-23.05";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
    nixos-generators.url = "github:nix-community/nixos-generators";
    nixos-generators.inputs.nixpkgs.follows = "nixpkgs";
    nixos-hardware.url = "github:NixOS/nixos-hardware";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix/1.42.1";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs = inputs@{ self, nixpkgs, home-manager, poetry2nix, flake-utils, ... }:
    let
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
          thymis-controller = pkgs.callPackage ./controller { poetry2nix = poetry2nix.legacyPackages.${system}; };
        }
      );
      nixosModules.thymis = ./thymis-nixos-module.nix;
    };
}
