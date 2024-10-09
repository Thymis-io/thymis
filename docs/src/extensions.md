# Extensions (Under Development)

In the **External Repositories** section of the sidebar, you can add external repositories to the Repository managed by Thymis.

<div class="warning">
The format of external repositories is still under active development, and we are working on improving the process of adding and managing external repositories in the Thymis controller.
Extensions may need to be updated to reflect future changes in the format of external repositories.
</div>

We are handling external repositories using the **Nix Flake** system. This allows you to add repositories from various sources, such as GitHub, GitLab, or any other Git repository.

If a repository is added to the Thymis controller, and contains the string "contains thymis modules" in the `README.md` file, the Thymis controller will automatically detect the repository as a Thymis module repository.

It will be added to the `PYTHONPATH` of the Thymis controller, and the modules will be available for use in the Thymis controller.

The current format of an external repository is as follows:

```
.
├── README.md
├── pyproject.toml # Optional
├── poetry.lock # Optional
├── flake.nix
└── python_module_name
    ├── __init__.py
    └── modules.py
```

The `pyproject.toml` and `poetry.lock` files are optional and can be used to manage dependencies for the module during development.

The `modules.py` file should contain subclasses of `thymis_controller.modules.Module` that define the module's functionality.
