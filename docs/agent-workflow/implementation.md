# Implementation phase

Read while the Issue is in `phase:ready` or `phase:implementation`.

## Start

Before editing:

1. Re-read the approved Issue and confirm no newer decision supersedes it.
2. Run `agent-context.* <issue>` to identify affected components and conditional application profiles.
3. Read only the linked relevant specification/design/status owners routed for this work.
4. If an Implementation Contract was supplied, save its exact bytes, then verify or restore its approved Issue comment pointer. Use `publish-implementation-contract.*` only after the Issue and contract approval gates; use `restore-implementation-contract.* --replace-stale` only for an intentional local version change.
5. Run `prepare-self-review.* <issue>`.
6. For source changes, run `start-feature-branch.* <issue> <short-description>`.
7. Replace `phase:ready` with `phase:implementation`.
8. Confirm upstream specification/design updates are approved.

## Implementation rules

- Stay inside approved scope and implement against the approved semantic owner documents.
- Do not mix unrelated cleanup or change a specification to make a bug appear conformant.
- Do not invent material API/architecture decisions in code. Return to requirements/design if a material contract or architecture requirement is missing or contradicted.
- Add/update tests for behavior and high-risk design invariants.
- Keep documentation responsibilities synchronized. Maintain clickable references when documents move or split.
- Keep task chronology and actual run results out of durable specifications/designs; put them in Issue/PR or status/evidence.

## Verification

During iteration, run the configured `verify_quick` hook from the [project profile](../../docs/agents/project.md):

```text
run-hook.* verify_quick
```

When an Issue has `## Affected components`, prefer `run-hook.* verify_quick --issue <issue>` so only those component hooks run. `verify_final` defaults to all components. Use `--capability <id>` only when the target capability is explicitly available; a skipped target was not verified.

When stable, run the configured `verify_final` hook and [document validation](../../scripts/agent/README.md):

```text
run-hook.* verify_final
validate-docs.*
```

Project hooks are defined by `.agent/project.json`. Record actual results against the verified HEAD in the appropriate evidence location.
If host-specific targets are reported as `SKIPPED_TARGET_VERIFICATION`, list them under the PR's `Untested / residual risk`; do not report them as verified.

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

After the local validator passes and the commit is pushed, open/update a Draft PR with `Closes #<issue>`, verification, untested platforms/targets, and a Generic profile rationale when an affected component is `generic`. Publish the self-review through `publish-self-review.* <issue> --pr <pr>`; that command re-fetches the single comment by ID and verifies its Checklist and HEAD before updating the PR pointer.

## Delivery gate

Before reporting implementation complete:

- changes committed;
- configured final verification passed or an exact self-hosting limitation and direct equivalent are recorded;
- docs validation passed;
- self-review validation passed;
- branch pushed;
- Draft PR exists with `Closes #<issue>` and complete Verification/Untested fields;
- Issue moved to `phase:review`.

Publish the public Self-review, mark the PR ready, wait for Required Checks, and run `delivery-check.* <issue> --pr <pr> --stage handoff`. This gate fails if checks are unconfigured, pending, or failing. Then enter the [review workflow](review.md).
