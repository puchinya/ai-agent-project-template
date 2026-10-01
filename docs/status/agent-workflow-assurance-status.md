# Agent Workflow Assurance Status

- Related spec: [Agent Workflow Assurance Specification](../specs/agent-workflow-assurance-spec.md)
- Related design: [Agent Workflow Assurance Design](../design/agent-workflow-assurance-design.md)

## Current state

Issue #5 is in `phase:review`. The remediation fixes starter-profile handoff validation, original Contract Section 9 checklist parsing, GitHub Required Check source semantics, closed-Issue phase routing, merge-label cleanup, and rendered contract-comment sizing. The exact original contract is published once on Issue #5 and its pointer and SHA are verified. PR #6 is open and Ready for review.

## Implemented

- Contract comments are byte-verified against a local recovery mirror and Issue pointer.
- Public Self-review evidence binds the Issue checklist, PR, and reviewed HEAD; delivery checks cover handoff and merge cleanup.
- Schema-2 Target requirements, Issue-scoped Quick selection, and Document impact owner routing are implemented.
- Handoff validates the schema-2 `initialized:false` starter without rewriting it. Checklist extraction recognizes the original Section 9 heading and keeps canonical blocks first.
- Required Checks honor exact App sources, source-unrestricted and legacy contexts, and GitHub's passing check-run conclusions. Closed Issues report `phase=closed`; merge cleanup removes only stale `phase:review`.
- Contract publication rejects rendered comments above 65,536 characters before remote mutation while retaining the 64 KiB raw-byte cap and exact SHA semantics.
- Cross-platform wrappers, workflow documentation, template indexes/manifest, and the CI matrix are updated.

## Delivery state

- `main` requires the four supported CI matrix checks and `PR metadata and public evidence`, all from GitHub Actions app `15368`; checks require an up-to-date branch and apply to administrators.
- Issue #5 and PR #6 remain open for review. Merge and Issue acceptance are not claimed.

## Verification state

- 88 local Python tests pass, including remediation regressions.
- `py_compile`, `validate-docs` (5 owners, 0 warnings), and `git diff --check` pass. The starter profile remains `initialized:false`.
- PR CI run `36887176833` passed all four matrix jobs and `PR metadata and public evidence` on implementation HEAD `a33c30ad`.
- The configured `verify_final` dispatcher requires an initialized profile, which this reusable starter intentionally does not have. Its configured `validate-docs` command was run directly and passed; CI also validates the template documentation.
