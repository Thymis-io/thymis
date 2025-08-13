# Update

In the main toolbar, you will find the **Update** button.

![Update Button](./update-button.png)

Unlike [**Commit**](commit.md) or [**Build**](build.md) which focus on your immediate project changes, **Update** specifically manages the external dependencies (called "inputs") in your project. In the background, this command runs `nix flake update` to fetch the latest revisions of all declared inputs.

## What does Update do?

Clicking **Update** will:

- Fetch the latest available versions of all Nix Flake inputs in your project
- Update your `flake.lock` file with the new input revisions
- Automatically rebuild your project with the new inputs

This is particularly useful when:
- You want to get the latest versions of upstream packages or tools
- You depend on external repositories that have released new features or bug fixes
- You need to update security patches from nixpkgs or other inputs

## Inputs in Thymis

Inputs include:
- The base Thymis repository
- External repositories added via [External Repositories](../../external-projects/external-repositories.md)
- Any other Git repository used in your Nix expressions

When you add an external repository to your project, it becomes an input that can be updated.

## Tasks and Results

When you trigger an update, Thymis creates an **Update Inputs** task visible in the **Tasks** view.

- If the update **succeeds**: Your project is rebuilt with the new inputs, and your `flake.lock` is updated.
- If the update **fails**: Click **View** on the task in the **Tasks** table to inspect the logs and determine the cause.

You can also view the task at any time during execution by clicking **View**.

![Update Task](./update-task.png)

Common issues during updates include:
- Incompatible changes in external repositories
- Network connectivity problems
- SHA256 mismatches during Git fetches

## When to use Update

Use **Update** to:

- Keep your project dependencies current with upstream changes
- Security updates from nixpkgs and other critical inputs
- Access new features or bug fixes from modules in external repositories
- Resolve issues that might be fixed in newer versions of dependencies

## After Update

Once the update completes successfully:

1. Review the changes in the commit dialogue that appears
2. Click **Commit** to save the new `flake.lock` and any rebuild changes
3. Optionally, test your updated configuration with **Build**
4. Deploy to devices if everything works as expected

**Tip:** Regularly updating your inputs helps keep your project secure and current with the latest improvements in the ecosystem.

## Best Practices

- Test updates with **Build** before committing and deploying to production devices
- Review changelogs of critical inputs before updating
- Consider updating to stable releases rather than always using latest
- Start with a small subset of devices when testing updates that might change significant functionality
