{ buildNpmPackage
, runtimeShell
, nodejs_22
, lib
}:
buildNpmPackage {
  pname = "thymis-frontend";
  version = "0.0.1";
  src = ./.;
  npmDepsHash = "sha256-UweENfcsKEJ8bMQhLs+uCD4XvkhSdNYuarE6uLOTzgM=";
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
