{
  description = "Thymis";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-23.05";
    home-manager.url = "github:nix-community/home-manager/release-23.05";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs@{ self, nixpkgs, home-manager }: 
  let 
    supported-systems = [ "x86_64-linux" "aarch64-linux" ];
    forAllSystems = nixpkgs.lib.genAttrs supported-systems;
  in rec {

    download-image = { thymis-config ? throw "thymis-config is required. Provide with --argstr" }:
      let
        thymis-config-parsed = builtins.fromJSON thymis-config;
      in
      (nixpkgs.lib.nixosSystem {
        modules = [
          nixosModules.thymis
        ];
        specialArgs = {
          inherit inputs;
          thymis-config = thymis-config-parsed;
        };
      }).config.system.build.download-path;
    packages = forAllSystems (system: 
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        thymis-frontend = pkgs.callPackage ./frontend { };
      }
    );
    nixosModules.thymis = ./thymis-nixos-module.nix;
  };
}
