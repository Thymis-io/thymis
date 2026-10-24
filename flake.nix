{
  description = "Thymis";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    home-manager.url = "github:nix-community/home-manager/release-26.05";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
    nixos-generators.url = "github:nix-community/nixos-generators";
    nixos-generators.inputs.nixpkgs.follows = "nixpkgs";
    nixos-raspberrypi.url = "github:nvmd/nixos-raspberrypi/main";
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
    # Only used for openssh 10.6p1 (see `securityModule` below): the 26.05 channel still
    # ships 10.5p1, which is affected by nine CVEs, and a hand `overrideAttrs` bump to 10.6
    # does not build.  nixos-unstable carries 10.6p1 and is cache-backed at 02c087f3fe67.
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  nixConfig = {
    extra-substituters = [
      "https://cache.thymis.io"
      "https://nixos-raspberrypi.cachix.org"
    ];
    extra-trusted-public-keys = [
      "cache.thymis.io-1:pEeKkNXiK17TLKls0KM8cEp0NGy08gc5chAmCyuQo8M="
      "nixos-raspberrypi.cachix.org-1:4iMO9LXa8BqhU+Rpg6LQKiGa2lsNh/j2oiYLNOQ5sPI="
    ];
  };

  outputs = inputss@{ self, nixpkgs, home-manager, flake-utils, ... }:
    let
      inputs = inputss // {
        thymis = self;
      };
      forAllSystems = nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" ];

      # 2026-10 security remediation.  The gaps the pinned nixos-26.05 channel does not
      # carry yet (brotli 1.2.1, curl 8.23.0, c-ares 1.34.9, node 22.23.4/24.22.1/26.12.1,
      # bun 1.4.4) live in `overlays/security-2026-10.nix`; the file header lists the CVEs
      # and why nothing the pin already fixes is overlaid.  Applied to every pkgs this flake
      # instantiates plus the four controller images below, so no vulnerable copy is left in
      # an artifact we publish.
      securityOverlay = import ./overlays/security-2026-10.nix;
      pkgsFor = system: import nixpkgs {
        inherit system;
        overlays = [ securityOverlay ];
      };

      # openssh 10.6p1 — nine CVEs in 10.5p1 (CVE-2026-106552/-106553/-106555/-106582..-106587),
      # and no 26.05 channel carries the fix yet.  A hand `overrideAttrs` to 10.6 does not
      # build, so take the whole package from the nixos-unstable input (cache-backed).
      securityModule = { pkgs, ... }: {
        nixpkgs.overlays = [ securityOverlay ];
        services.openssh.package =
          inputs.nixpkgs-unstable.legacyPackages.${pkgs.stdenv.hostPlatform.system}.openssh;
      };

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
        system.stateVersion = "26.05";
      };

      thymis-controller-pi-3-sd-image = (nixpkgs.lib.nixosSystem {
        modules = [
          nixosModules.thymis-device
          nixosModules."thymis-device-raspberry-pi-3"
          nixosModules."thymis-image-sd-card-image"
          nixosModules.thymis-controller
          activate-thymis-controller-module
          securityModule
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
          securityModule
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
          securityModule
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
          securityModule
        ];
        specialArgs = {
          inherit inputs;
        };
      }).config.system.build.thymis-image-with-secrets-builder-x86_64;

    in
    {
      inputs = inputs;
      formatter = forAllSystems (system: (pkgsFor system).nixpkgs-fmt);
      devShells = forAllSystems (system:
        let
          pkgs = pkgsFor system;
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.uv
              pkgs.python313
              pkgs.nodejs_24
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
              pkgs.nodejs_24
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
              pkgs.nodejs_24
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
          pkgs = pkgsFor system;
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
