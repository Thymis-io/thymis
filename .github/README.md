The goal is to ensure tasks run on either the `pull_request` or `pull_request_target` events, but not both.

The fundamental difference between the two events is:
- `pull_request_target`: Starts from the PR target and has secrets access.
- `pull_request`: Starts from the PR synthesized merge commit and has no secrets access.

We want the following to happen:
- If we trust the code, run the build in the context of the PR target with secrets access.
- If we don't trust the code, run the build in the context of the PR synthesized merge commit without secrets access.

We trust the code if any of the following conditions are met:
1. The PR author is a member of the organization.
2. The PR is tagged with a label that indicates trust.

The logic to determine if we trust the code:
```yaml
trust_code = ${{ github.event.pull_request.author_association == 'MEMBER' || contains(github.event.pull_request.labels.*.name, 'trust') }}
```

To restrict, we build the following logic:
```yaml
((not in_pull_request_target) OR trust_code) AND ((not in_pull_request) OR (not trust_code))
```

Let's verify this condition with inputs `in_pull_request_target`, `in_pull_request`, and `trust_code` (where both `in_pull_request_target` and `in_pull_request` cannot be true at the same time):

For `trust_code = true`:
- `in_pull_request_target = false`, `in_pull_request = false`:
    ```yaml
    ((not false) OR true) AND ((not false) OR (not true)) = (true OR true) AND (true OR false) = true AND true = true
    ```
- `in_pull_request_target = false`, `in_pull_request = true`:
    ```yaml
    ((not false) OR true) AND ((not true) OR (not true)) = (true OR true) AND (false OR false) = true AND false = false
    ```
- `in_pull_request_target = true`, `in_pull_request = false`:
    ```yaml
    ((not true) OR true) AND ((not false) OR (not true)) = (false OR true) AND (true OR false) = true AND true = true
    ```

For `trust_code = false`:
- `in_pull_request_target = false`, `in_pull_request = false`:
    ```yaml
    ((not false) OR false) AND ((not false) OR (not false)) = (true OR false) AND (true OR true) = true AND true = true
    ```
- `in_pull_request_target = false`, `in_pull_request = true`:
    ```yaml
    ((not false) OR false) AND ((not true) OR (not false)) = (true OR false) AND (false OR true) = true AND true = true
    ```
- `in_pull_request_target = true`, `in_pull_request = false`:
    ```yaml
    ((not true) OR false) AND ((not false) OR (not false)) = (false OR false) AND (true OR true) = false AND true = false
    ```

Definitions:
- `in_pull_request_target`:
    ```yaml
    ${{ github.event_name == 'pull_request_target' }}
    ```
- `in_pull_request`:
    ```yaml
    ${{ github.event_name == 'pull_request' }}
    ```

Final condition for `should_run_job`:
```yaml
${{ (( ! (github.event_name == 'pull_request_target') ) || (github.event.pull_request.author_association == 'MEMBER' || contains(github.event.pull_request.labels.*.name, 'trust')) ) && (( ! (github.event_name == 'pull_request') ) || ( ! (github.event.pull_request.author_association == 'MEMBER' || contains(github.event.pull_request.labels.*.name, 'trust')) )) }}
```
