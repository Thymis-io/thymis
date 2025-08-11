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
    license = licenses.mit;
    maintainers = with maintainers; [ yourName ];
  };
}
```
