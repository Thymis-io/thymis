# Auto-Update

Auto-Update lets Thymis automatically keep your devices up to date without manual intervention. On the configured schedule it:

1. Runs `nix flake update` to pull in the latest versions of all Nix inputs (nixpkgs, Thymis modules, external repositories).
2. Commits the updated `flake.lock` to the project repository.
3. Deploys the new configuration to every connected device.

## Enabling Auto-Update

1. In the sidebar, click **Auto-Update**.
2. Toggle **Enable Auto-Update** on.
3. Configure the schedule (see below).
4. Click **Save**.

## Configuring the Schedule

### Frequency

| Frequency | Description |
|---|---|
| **Hourly** | Fires every hour at the configured minute. |
| **Daily** | Fires once per day at the configured time. |
| **Weekly** | Fires on the selected days of the week at the configured time. |
| **Monthly** | Fires on a specific day of the month (1–28) at the configured time. |
| **Monthly (by weekday)** | Fires on the *n*th occurrence of a specific weekday in the month (e.g. "first Monday", "last Friday"). |

### Default schedule

The default schedule fires weekly on **Monday through Thursday at 03:00 UTC**. This avoids weekend fire times while leaving Friday–Sunday free for manual work.

### Time of Day

For all frequencies except **Hourly**, you can set the **Time of Day** (UTC). The controller always interprets this time as UTC regardless of the timezone of the devices.

### Weekly: Days of the Week

When **Weekly** is selected, choose one or more days to fire on. At least one day must be selected.

### Monthly: Day of Month

When **Monthly** is selected, choose a day between 1 and 28. Days 29–31 are not available to avoid invalid dates in short months.

### Monthly (by weekday): Occurrence and Weekday

When **Monthly (by weekday)** is selected, two dropdowns appear:

- **Which occurrence** — First, Second, Third, Fourth, Fifth, or Last.
- **Day of the week** — Monday through Sunday.

If the selected occurrence does not exist in a given month (e.g. "fifth Monday" in a month with only four Mondays), that month is skipped and the update fires in the next month that has the occurrence.

## Running an Update Immediately

Click **Run Now** on the Auto-Update page to trigger an auto-update immediately, regardless of the configured schedule.

## Working State Warning

Before running, Thymis stashes any uncommitted changes in the project repository with `git stash`, performs the update and deploy, then restores the stash with `git stash pop`. This means:

- **Uncommitted changes will be temporarily hidden** during the update. They are restored afterwards.
- If the update fails mid-run, the stash is still present and can be restored manually with `git stash pop`.
- It is best practice to commit or discard any open changes before a scheduled update fires.

## See also

- [Deploy an Update](update.md)
- [Tasks](../reference/ui/tasks.md)
- [Project repository](../reference/concepts/project-repository.md)
