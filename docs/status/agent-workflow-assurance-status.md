# Agent Workflow Assurance Status

- Related spec: [Agent Workflow Assurance Specification](../specs/agent-workflow-assurance-spec.md)
- Related design: [Agent Workflow Assurance Design](../design/agent-workflow-assurance-design.md)

## Current state

Issue #5 is in `phase:review`. The current remediation candidate additionally fixes starter-profile handoff validation, original Contract Section 9 checklist parsing, GitHub Required Check source semantics, closed-Issue phase routing, merge-label cleanup, and rendered contract-comment sizing.

## Implemented

- Contract comments are byte-verified against a local recovery mirror and Issue pointer.
- Public Self-review evidence binds the Issue checklist, PR, and reviewed HEAD; delivery checks cover handoff and merge cleanup.
- Schema-2 Target requirements, Issue-scoped Quick selection, and Document impact owner routing are implemented.
- Handoff validates the schema-2 `initialized:false` starter without rewriting it. Checklist extraction recognizes the original Section 9 heading and keeps canonical blocks first.
- Required Checks honor exact App sources, source-unrestricted and legacy contexts, and GitHub's passing check-run conclusions. Closed Issues report `phase=closed`; merge cleanup removes only stale `phase:review`.
- Contract publication rejects rendered comments above 65,536 characters before remote mutation while retaining the 64 KiB raw-byte cap and exact SHA semantics.
- Cross-platform wrappers, workflow documentation, template indexes/manifest, and the CI matrix are updated.

## Known gaps

- The exact original Implementation Contract still needs publication and pointer verification before the Ready-only PR metadata check can pass.
- `main` has no branch protection or configured Required Checks; handoff remains fail-closed until those contexts are configured and green.
- PR #6 remains Draft, so its Ready-only metadata job has not evaluated this remediation candidate.

## Verification state

- 86 local Python tests pass, including remediation regressions.
- `py_compile`, `validate-docs` (5 owners, 0 warnings), and `git diff --check` pass. The profile remains `initialized:false`.
- The prior PR matrix passed on Ubuntu, Windows, and macOS (4 jobs) at HEAD `b9deb750`; CI for the remediation HEAD is pending.
- The Windows PowerShell wrapper smoke passed on the prior CI run. The PR metadata job was skipped while the pull request remained Draft.
