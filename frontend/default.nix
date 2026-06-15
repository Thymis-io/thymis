{ buildNpmPackage
, runtimeShell
, nodejs_24
, runCommand
, git-rev
, lib
}:
let
  version = (builtins.fromJSON (builtins.readFile ./package.json)).version;

  # The SvelteKit/Vite build produces architecture-independent static JS.
  # buildNpmPackage / runCommand here come from the *build host's* package set
  # (see flake.nix, which calls this from the x86_64 set), so the Node/Vite
  # build runs natively and never under qemu.  Building the frontend under qemu
  # crashes with "qemu: uncaught target signal 4 (Illegal instruction)" because
  # qemu's user-mode emulation mishandles some instructions V8's JIT emits.
  frontend-static = buildNpmPackage {
    GIT_REV = git-rev;
    pname = "thymis-frontend-static";
    inherit version;
    src = ./.;
    npmDepsHash = "sha256-/lq4a2ayJpxo5HWebSWsvmpTHhoHP4sces5adORUPOA=";
    dontNpmInstall = true;
    installPhase = ''
      runHook preInstall

      mkdir -p $out
      cp -r ./build/* $out

      runHook postInstall
    '';
  };
in
# The wrapper only copies the static bundle and writes a launcher script that
  # references the *target* node (nodejs_24 is overridden to the target arch in
  # flake.nix).  No code is executed at build time, so this also builds natively;
  # the target node is just a runtime dependency.
runCommand "thymis-frontend-${version}" { } ''
  mkdir -p $out/lib/thymis-frontend/build
  cp -r ${frontend-static}/* $out/lib/thymis-frontend/build
  mkdir -p $out/bin
  cat > $out/bin/thymis-frontend <<EOF
  #!${runtimeShell}
  ${nodejs_24}/bin/node $out/lib/thymis-frontend/build/index.js
  EOF
  chmod +x $out/bin/thymis-frontend
''
