# Agent Workflow Assurance Status

- Related spec: [Agent Workflow Assurance Specification](../specs/agent-workflow-assurance-spec.md)
- Related design: [Agent Workflow Assurance Design](../design/agent-workflow-assurance-design.md)

## Current state

Issue #5 requirements and the approved assurance and project-profile specification/design owners are implemented in the current candidate. Contract distribution, public Self-review validation, delivery checks, Target gating, and read-only CI assurance are implemented locally.

## Implemented

- Contract comments are byte-verified against a local recovery mirror and Issue pointer.
- Public Self-review evidence binds the Issue checklist, PR, and reviewed HEAD; delivery checks cover handoff and merge cleanup.
- Schema-2 Target requirements, Issue-scoped Quick selection, and Document impact owner routing are implemented.
- Cross-platform wrappers, workflow documentation, template indexes/manifest, and the CI matrix are updated.

## Known gaps

- GitHub platform-matrix jobs and Required Checks still need to run against a pushed pull request.
- The Issue contract pointer and public Self-review handoff evidence are not yet published.

## Verification state

- 80 local Python tests pass.
- `py_compile`, `validate-docs` (5 owners, 0 warnings), and the configured `verify_final` hook pass.
- All seven new Unix wrappers start and show help successfully; Windows wrapper smoke and the remote CI matrix remain pending.
