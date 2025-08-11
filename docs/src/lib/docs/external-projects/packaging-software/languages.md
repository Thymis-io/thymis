# Languages

In Thymis, you can package software written in various programming languages using Nix. This section provides an overview of how to package software for different languages, including Python, Node.js, C. Other languages can be added similarly.

## Python

To package Python applications, you can use the `python3Packages` set provided by Nixpkgs. Here's a simple example of how to create a Python package:

```nix
{ lib, python3Packages }:
python3Packages.buildPythonPackage rec {
  pname = "my-python-app";
  version = "1.0";
  src = ./.;

  propagatedBuildInputs = with python3Packages; [
    requests
    flask
  ];

  meta = with lib; {
    description = "A simple Python application";
  };
}
```

This Nix expression defines a Python package named `my-python-app` with version `1.0`. It specifies the source directory and the dependencies required for the application, such as `requests` and `flask`.

The python project should be a [PEP 517](https://peps.python.org/pep-0517/) compliant project.

See the [Nixpkgs Python documentation](https://nixos.org/manual/nixpkgs/stable/#building-packages-and-applications) for more details on packaging Python applications.

## Node.js

To package Node.js applications, you can use the `buildNpmPackage` function provided by Nixpkgs. Here's an example of how to create a Node.js package:

```nix
{ lib, buildNpmPackage, fetchFromGitHub }:
buildNpmPackage rec {
  pname = "my-node-app";
  version = "1.0";
  src = fetchFromGitHub {
    owner = "my-org";
    repo = "my-node-app";
    rev = "v${version}";
    sha256 = "sha256-hash-of-the-source";
  };
  buildInputs = [ nodejs ];
  npmDepsHash = "sha256-hash-of-npm-dependencies";
  meta = with lib; {
    description = "A simple Node.js application";
  };
}
```

Where `sha256-hash-of-the-source` is the SHA256 hash of the source code archive, and `sha256-hash-of-npm-dependencies` is a hash of the pre-fetched npm dependencies from the `package-lock.json` file.

See the [Nixpkgs Node.js documentation](https://nixos.org/manual/nixpkgs/stable/#javascript-buildNpmPackage) for more details on packaging Node.js applications.

## C/C++

Nixpkgs provides hooks for different build systems such as make, cmake, autotools, etc. Here's an example of how to package a C application using `stdenv.mkDerivation`:

```nix
{ stdenv, fetchFromGitHub }:
stdenv.mkDerivation rec {
  pname = "my-c-app";
  version = "1.0";
  src = fetchFromGitHub {
    owner = "my-org";
    repo = "my-c-app";
    rev = "v${version}";
    sha256 = "sha256-hash-of-the-source";
  };
  meta = with stdenv.lib; {
    description = "A simple C application";
  };
}
```

This Nix expression defines a C application named `my-c-app` with version `1.0`. It specifies the source directory and the dependencies required for the application. If you properly set up your `Makefile` or `CMakeLists.txt`, Nix will automatically handle the build process as well as locating the necessary libraries and headers and locating the binary in the build output.

See the [Nixpkgs hooks reference](https://nixos.org/manual/nixpkgs/stable/#chap-hooks) for more details on packaging C/C++ applications and similiar.

## Conclusion

You have seen 3 examples of how to package software for different programming languages using Nix. Each language has its own set of functions and conventions, but the general principles of defining a package, specifying dependencies, and providing metadata remain consistent.
You can find more information on packaging software in the [Nixpkgs manual](https://nixos.org/manual/nixpkgs/stable/) and the [Nixpkgs search](https://search.nixos.org/packages) to find available packages and their configurations as well as a link to their source code.
We encourage you to explore resources and examples for the specific language you are working with online, as the Nix community provides extensive documentation and examples for various languages and frameworks.
