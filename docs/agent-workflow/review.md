# Review phase

Read while the associated PR is open or the Issue is in `phase:review`.

The Issue/specification remains the approved behavior. Design remains the approved durable architecture. The PR describes actual delta and evidence.

## PR structure

```text
## Purpose / impact
## Delta
## Design deviations
## Verification
## Untested / residual risk
## Reviewer focus
Closes #<issue>
```

Do not duplicate the full Issue/spec/design/Implementation Contract.

## Review handling

For each actionable review item:

- implement it; or
- explain why no change is appropriate; or
- create a follow-up Issue for valid out-of-scope work.

After repository-changing remediation:

1. focused verification;
2. commit;
3. inspect the complete diff again;
4. refresh and redo self-review on the new HEAD;
5. rerun final verification when required;
6. rerun docs validation.

If review requires a material requirement/design change, return to `phase:design`.

## Completion

Work is complete only when required reviews/checks pass, acceptance criteria are satisfied, required docs are synchronized, and the PR is merged.

Verify Issue closure after merge.
