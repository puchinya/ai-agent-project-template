# Review phase

Read while the associated PR is open or the Issue is in `phase:review`.

The Issue and its semantic specification owners remain the approved behavior. Design remains the approved durable architecture. The PR describes actual delta and evidence.

Run `agent-context.* <issue>` to identify the affected components and selected conditional application profiles. Focus review on those profiles and the relevant linked owners; do not load all standards or durable documents by default.

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

Keep the PR body limited to the review summary and machine-checked fields. The `## Self-review` block contains only the public comment ID, SHA-256, and Reviewed-HEAD; the full checklist results live in one top-level PR conversation comment. Complete `## Verification` and `## Untested` before handoff. If an affected component uses `generic`, give a concrete reason under `## Generic profile rationale`.

Do not duplicate the full Issue/spec/design/Implementation Contract.

## Documentation review

Check that:

- specification and design responsibilities remain separate;
- each durable rule has one semantic owner and other documents link to it;
- durable documents describe current state rather than Issue/PR/test chronology;
- the human-readable Overview agrees with the detailed contract/architecture;
- relevant commercial-quality topics are covered or explicitly N/A with a concrete reason;
- cross-document navigation is clickable and valid;
- no material decision is hidden in code and no duplicate normative/design owner was introduced.

If a material requirement/design gap is found, return to `phase:design`.

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

## Completion

Work is complete only when required reviews/checks pass, acceptance criteria are satisfied, required docs are synchronized, and the PR is merged.

Verify Issue closure after merge, then run `finalize-merged-issue.* <issue> --pr <pr>` to remove remaining `phase:*` labels. The cleanup is idempotent.

Before requesting handoff, run `validate-public-review.* <issue> --pr <pr>` and `delivery-check.* <issue> --pr <pr> --stage handoff`. Reviewers independently inspect the diff, evidence, and Required Checks; self-review evidence is a navigation aid, not proof of test truth.
