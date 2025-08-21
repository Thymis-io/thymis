{ callPackage
, pyproject-nix
, lib
, pyproject-build-systems
, uv2nix
, writeShellApplication
, python313
, shadow
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

  env = (pythonSet.mkVirtualEnv "thymis-agent-env" workspace.deps.default).overrideAttrs (oldAttrs: {
    venvIgnoreCollisions = [
      "bin/fastapi"
    ];
  });

  app = writeShellApplication {
    name = "thymis-agent";
    runtimeInputs = [ shadow ];
    text = ''
      exec ${env}/bin/thymis-agent "$@"
    '';
  };
in
app
