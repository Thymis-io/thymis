{ buildNpmPackage
, runtimeShell
, nodejs_22
, git-rev
, lib
}:
buildNpmPackage {
  GIT_REV = git-rev;
  pname = "thymis-frontend";
  version = "0.0.1";
  src = ./.;
  npmDepsHash = "sha256-DHzXo1p6iHhTvW2wVRbIfVVMcv5oxlVY78AazP1MVo4=";
  postInstall = ''
    mkdir -p $packageOut/build
    cp -r ./build/* $packageOut/build
    # create bin/thymis-frontend
    mkdir -p $out/bin
    cat > $out/bin/thymis-frontend <<EOF
    #!${runtimeShell}
    ${nodejs_22}/bin/node $packageOut/build/index.js
    EOF
    chmod +x $out/bin/thymis-frontend
  '';
}
