{ buildNpmPackage
, runtimeShell
, nodejs_22
, git-rev
, lib
}:
buildNpmPackage {
  GIT_REV = git-rev;
  pname = "thymis-frontend";
  version = (builtins.fromJSON (builtins.readFile ./package.json)).version;
  src = ./.;
  npmDepsHash = "sha256-ZJC2yhSzBivDYgtcVnUS5aL9T6svydtxl6tL/2U4b9Q=";
  dontNpmInstall = true;
  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/thymis-frontend/build
    cp -r ./build/* $out/lib/thymis-frontend/build
    mkdir -p $out/bin
    cat > $out/bin/thymis-frontend <<EOF
    #!${runtimeShell}
    ${nodejs_22}/bin/node $out/lib/thymis-frontend/build/index.js
    EOF
    chmod +x $out/bin/thymis-frontend

    runHook postInstall
  '';
}
