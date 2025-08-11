# External repositories/Inputs

External repositories (also called inputs) are the way that Thymis brings additional Nix expressions, Thymis modules, and other resources into a project.
They are implemented using Nix Flakes – the same declaration‑style that powers NixOS and Nixpkgs – and are managed from the Thymis UI.

In Thymis, an input is a Git repository that satisfies the following conditions:
- It contains a valid `flake.nix` file at its root.
- The repository is accessible via a Git URL (HTTPS or SSH).

Inputs can provide Thymis modules if they satisfy the following conditions:
- They contain a `README.md` file at their root that contains the string `contains thymis modules`.
- They contain `python_modules_unique_path/python_module_name.py` files that define Thymis modules by sub-classing `thymis_controller.module.ThymisModule`.

See [your first Thymis module](../../external-projects/thymis-modules/first-module.md) for more information on how to create a Thymis module and structure the files in your repository.

See [external repositories](../../external-projects/external-repositories.md) for more information on how to set up and use external repositories in your Thymis project.

The repositories added to the project are included as Nix Flake inputs, which means that you can update them using the **Update** button in the Thymis UI.
This will fetch the latest changes from the repository and update the inputs in your project.

## Implementation Details

Inputs are implemented as Nix Flakes, which means that they can be used to provide additional Nix expressions, Thymis modules, and other resources to your Thymis project.

Check out the [Nix Wiki on Flakes](https://wiki.nixos.org/wiki/Flakes) for more information on how to create a Nix flake file and use it in your project.

If you have access to your project repository, as described in [Accessing the Thymis project git repository](../../external-projects/git-repository.md), you can inspect the generated `flake.nix` file in your project repository to see how the inputs are defined.

The Syntax of the Git URL for the input is described at the [Nix Flakes documentation](https://nix.dev/manual/nix/2.24/command-ref/new-cli/nix3-flake).
Examples of valid Git URLs are:
    - `git+https://example.org/my/repo`
    - `git+https://example.org/my/repo?dir=subdir`
    - `git+ssh://example.org/my/repo?ref=v1.2.3`
    - `git+ssh://example.org/my/repo?ref=branch-name&rev=abcd1234`
