{ callPackage
, pyproject-nix
, lib
, pyproject-build-systems
, uv2nix
, git
, nixpkgs-fmt
, nix
, writeShellApplication
, thymis-frontend
, openssh
, python313
, file
}:
let
  python = python313;

  workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

  overlay = workspace.mkPyprojectOverlay {
    # Prefer prebuilt binary wheels as a package source.
    # Sdists are less likely to "just work" because of the metadata missing from uv.lock.
    # Binary wheels are more likely to, but may still require overrides for library dependencies.
    sourcePreference = "wheel"; # or sourcePreference = "sdist";
    # Optionally customise PEP 508 environment
    # environ = {
    #   platform_release = "5.10.65";
    # };
  };

  pyprojectOverrides = final: prev: {
    http-network-relay = prev.http-network-relay.overrideAttrs (old: {
      buildInputs = (old.buildInputs or [ ]) ++ final.resolveBuildSystem ({ setuptools = [ ]; });
    });
  };

  pythonSet =
    # Use base package set from pyproject.nix builders
    (callPackage pyproject-nix.build.packages {
      inherit python;
    }).overrideScope
      (
        lib.composeManyExtensions [
          pyproject-build-systems.overlays.default
          overlay
          pyprojectOverrides
        ]
      );

  env = (pythonSet.mkVirtualEnv "thymis-controller-env" workspace.deps.default).overrideAttrs (oldAttrs: {
    venvIgnoreCollisions = [
      "bin/fastapi"
    ];
  });

  app = writeShellApplication {
    name = "thymis-controller";
    runtimeInputs = [ git nixpkgs-fmt nix env openssh file ];
    text = ''
      export UVICORN_HOST="''${UVICORN_HOST:=127.0.0.1}"
      export UVICORN_PORT="''${UVICORN_PORT:=8000}"
      export PYTHONENV=${env}
      export THYMIS_FRONTEND_BINARY_PATH=${thymis-frontend}/bin/thymis-frontend
      export THYMIS_ALEMBIC_INI_PATH="''${THYMIS_ALEMBIC_INI_PATH:=${./alembic.ini}}"
      exec ${env}/bin/uvicorn thymis_controller.main:app "$@"
    '';
  };
in
app
