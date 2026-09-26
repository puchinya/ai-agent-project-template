# Implementation phase

Read while the Issue is in `phase:ready` or `phase:implementation`.

## Start

Before editing:

1. Re-read the approved Issue and relevant spec/design.
2. Confirm no newer decision supersedes them.
3. If an Implementation Contract was supplied, save/verify its exact local mirror.
4. Run `prepare-self-review.* <issue>`.
5. For source changes, run `start-feature-branch.* <issue> <short-description>`.
6. Replace `phase:ready` with `phase:implementation`.
7. Confirm upstream spec/design updates are approved.

## Implementation rules

- Stay inside approved scope.
- Do not mix unrelated cleanup.
- Do not change a spec to match a bug.
- Do not invent material API/architecture decisions in code.
- Add/update tests for behavior and high-risk design invariants.
- Keep documentation responsibilities synchronized.
- If a material contract/architecture requirement is missing or contradicted, return to requirements/design.

## Verification

During iteration:

```text
run-hook.* verify_quick
```

When stable:

```text
run-hook.* verify_final
validate-docs.*
```

Project hooks are defined by `.agent/project.json`.

## Self-review

After repository-controlled changes are stable:

1. commit the implementation;
2. inspect the complete task diff against the default branch;
3. refresh `prepare-self-review.*`;
4. judge every effective checklist item as PASS/FAIL/N/A;
5. add concrete `Evidence:` for PASS and `Reason:` for N/A;
6. set `Reviewed-HEAD` to the current full commit SHA;
7. run `validate-self-review.*`.

Any new commit makes the prior self-review stale.

## Delivery gate

Before reporting implementation complete:

- changes committed;
- configured final verification passed;
- docs validation passed;
- self-review validation passed;
- branch pushed;
- PR exists with `Closes #<issue>`;
- Issue moved to `phase:review`.

Then enter `review.md`.
