<!-- agent-doc-type: specification -->
<!-- agent-doc-schema: 2 -->
# Agent Workflow Assurance Specification

- Status: Approved
- Owning Issue: #5
- Related design: [Agent Workflow Assurance Design](../design/agent-workflow-assurance-design.md)

## Overview

This specification defines the observable behavior of Issue contract distribution, independently verifiable PR self-review, implementation handoff checks, merge finalization, and repository-template CI assurance. The [Project Profile and Agent Context Specification](project-profile-spec.md) owns profile, Target, hook, and context-routing behavior. The [Agent Tooling Specification](agent-tooling-spec.md) remains the owner of documentation validation and template-update behavior.

## Purpose

Provide a recoverable, reviewable record of approved implementation scope and prevent incomplete or stale evidence from being reported as a successful handoff or merged delivery.

## Scope

### In scope

- GitHub Issue contract pointer and single-comment source format, local mirror, publish, restore, and verification commands.
- PR self-review publication and independent validation.
- Handoff and merged delivery checks, including Required Checks and merge-phase cleanup.
- CI metadata/evidence checks and trust boundaries for untrusted pull requests.
- Cross-platform wrappers for the commands defined here.

### Out of scope

- Adding workflow phases or changing the existing requirements/design/ready/implementation/review phase sequence.
- Replacing GitHub or the local Issue-scoped mirror with an external database or service.
- Changing Schema 1 behavior or the hook ordering owned by the Project Profile and Agent Context Specification.
- Treating an author's evidence form, self-review, capability declaration, or missing CI as independent proof of success.

## Terminology

| Term | Meaning |
|---|---|
| Contract source comment | The single top-level Issue comment whose exact payload bytes are identified by the Issue pointer. |
| Contract mirror | The local Issue-scoped copy of the verified contract payload and its SHA-256 record. |
| Reviewed HEAD | The exact 40-character commit SHA against which a self-review checklist was evaluated. |
| Handoff | The implementation-complete state verified before merge. |
| Required Check | A configured status check required by the repository for the PR's current head commit. |

## Semantic ownership

This document owns the contract, public review-evidence, delivery-check, finalization, and CI assurance behavior in its scope. Target requirements, component selection, hook execution, and context routing are owned by the [Project Profile and Agent Context Specification](project-profile-spec.md). Documentation validation and template refresh remain owned by the [Agent Tooling Specification](agent-tooling-spec.md).

## Normative requirements

### Contract distribution

- The CLI MUST provide:

  ```text
  save-implementation-contract N [path]
  publish-implementation-contract N [--source PATH] [--supersede]
  restore-implementation-contract N [--replace-stale]
  verify-implementation-contract N
  ```

- The Issue body section `## Implementation Contract` MUST contain only `Comment ID: <integer>`, `SHA-256: <64 lowercase hexadecimal characters>`, and `State: approved`. It MUST NOT contain the full contract.
- A contract source comment MUST be one top-level comment on the owning Issue. Its first line MUST be `<!-- agent-contract:v1 issue=N sha256=HEX bytes=DECIMAL -->`, followed by one blank line and the exact UTF-8 payload bytes.
- The SHA-256 and byte count MUST cover the original payload bytes exactly, including line endings and final newline. Publishing or restoring MUST NOT normalize, trim, or rewrite the payload.
- Contract payloads MUST be non-empty, at most 64 KiB, valid UTF-8, and free of NUL bytes and obvious credential material.
- Before any publish request, the fully rendered GitHub comment (version header, two newlines, and exact UTF-8 payload) MUST be at most 65,536 characters. This validation MUST be local, preserve the mirror, and reject without posting; the header makes the effective raw limit slightly lower for ASCII-heavy payloads. Payloads MUST NOT be truncated, split, normalized, or published as multiple comments.
- Publish MUST validate the target Issue, create or reuse the matching top-level comment, retrieve that comment by its single ID, and verify its Issue, byte count, and SHA-256 before updating the Issue pointer. If pointer update fails after comment creation, the comment remains and a same-SHA retry MUST reuse it.
- Publishing the same Issue and SHA MUST be idempotent. A different SHA MUST require `--supersede`; superseding MUST create a new comment and MUST NOT edit or delete the prior comment.
- Restore MUST retrieve only the comment named by the Issue pointer through `GET /repos/{owner}/{repo}/issues/comments/{id}`. It MUST verify comment ownership, Issue association, payload length, and SHA before any mirror replacement. It MUST NOT list or fetch every Issue comment.
- An invalid or mismatched comment, API 403/404, or conflicting local mirror MUST fail closed and leave the existing mirror bytes unchanged. Replacing a stale mirror requires `--replace-stale`; the previous payload MUST first be retained under a SHA-specific backup, followed by atomic replacement.
- An Issue body update MUST re-read the body immediately before changing only the contract section and MUST read the result back. Concurrent Issue-body editing is unsupported and MUST be reported because GitHub does not provide a strict compare-and-swap update here.
- `verify-implementation-contract` MUST validate the current pointer, named comment, and local mirror without fetching unrelated comments. Legacy local-only saved contracts remain readable.
- Normal `agent-context` output MUST NOT fetch or inline contract comments; it MAY report the local mirror's SHA and status.
- `agent-context` MUST request Issue state and derive `closed` before label-based phase routing. It MUST print `phase=closed` and an empty workflow for closed Issues. Checkpoint phase reporting MUST request Issue state; open Issues retain label-based routing.

### Self-review and delivery

- The CLI MUST provide:

  ```text
  publish-self-review N --pr P
  validate-public-review N --pr P [--head 40hex]
  delivery-check N --pr P --stage handoff|merged
  finalize-merged-issue N --pr P
  ```

- The complete self-review MUST be one top-level PR conversation comment. The PR body section `## Self-review` MUST contain only the comment ID, SHA-256, and Reviewed HEAD.
- The effective checklist MUST prefer a valid `AGENT_REVIEWER_CHECKLIST_V1` canonical block when present. Otherwise it MUST recognize only a `Reviewer Checklist` heading, optionally preceded by a numeric prefix such as `9.` and optionally followed by one ASCII- or Japanese-parenthesized qualifier; arbitrary headings that merely contain those words MUST NOT match.
- Effective checklist entries MUST combine Contract items in source order as `C001` onward, followed by Issue items in source order as `I001` onward.
- Self-review publication MUST first require the existing `validate-self-review` command to pass. It MUST then retrieve the named comment and independently verify its PR, SHA, Reviewed HEAD, and effective Reviewer Checklist.
- A self-review is stale whenever the PR head differs from its Reviewed HEAD. A new commit requires a new review and publication.
- Review evidence MUST identify concrete code, test, or CI evidence. Its format is not proof of truth; a reviewer in a separate session MUST verify the claims.
- `delivery-check --stage handoff` MUST require: the PR and Issue are in the same repository and match the requested Issue; the PR is open and non-draft; the PR body contains `Closes #N`; the Issue is in `phase:review`; the PR head equals the published Reviewed HEAD; the published self-review comment, SHA, and effective checklist validate; verification and untested fields are filled; and every configured Required Check for the current head is green.
- Handoff MUST schema-validate the project profile while accepting `initialized:false` for a distributed template starter. It MUST NOT initialize or rewrite that profile.
- A Required Check with `app_id >= 0` MUST match a check-run from that exact GitHub App. `app_id == -1`, a missing app ID, or a legacy `contexts[]` entry is source-unrestricted and MAY be satisfied by a matching check-run name from any app or a matching commit-status context. An app-specific check MUST NOT be satisfied by a commit status. Completed check-run conclusions `success`, `skipped`, and `neutral` pass; commit-status contexts pass only with state `success`. Missing, pending, and failing checks fail closed.
- `delivery-check --stage merged` MUST require a merged PR, a closed Issue, and no remaining phase label.
- `finalize-merged-issue` MUST verify merged/closed state before removing only a stale `phase:review` label. Any other `phase:*` label MUST fail closed without mutation. Repeated finalization after `phase:review` is gone MUST succeed without mutation.
- A generic profile is legal. Initialization MUST warn when a component uses `generic`. A PR that affects a generic component MUST include a concrete `Generic profile rationale:` explaining why the reported verification is valid for that component.

### CI and trust boundary

- The shared workflow MUST run on `pull_request` and pushes to `main`. Its test matrix MUST cover Ubuntu with Python 3.10 and 3.13, plus Windows and macOS with Python 3.13.
- CI MUST run the agent-tooling unittest suite, `py_compile`, and `validate-docs`. A separate PR-metadata/evidence job MUST be read-only. Draft PRs MAY defer the Ready-only evidence decision; Ready PRs MUST satisfy it.
- Untrusted PR code MUST NOT receive secrets or write tokens. The workflow MUST NOT use `pull_request_target` to execute untrusted PR hooks or code.
- A Required Check that is unconfigured, pending, or failed MUST NOT be treated as successful. Missing CI execution MUST remain unverified.
- Hook commands are trusted shell commands from the repository's initialized `.agent/project.json`. They are arbitrary local commands, not a sandbox. CI MUST NOT execute untrusted repository-configured hooks with write credentials.
- Temporary request JSON and contract/review payload files MUST be removed on success and ordinary failure/cancellation paths. Contract text and tokens MUST NOT appear in normal logs.

## Observable behavior

### State model

An Issue may have no contract pointer or one pointer to its approved source comment. A PR may have no published self-review or one pointer to its latest review. A published review is current only while its Reviewed HEAD equals the PR head. Handoff and merged delivery are separate checks; passing handoff does not imply merge or Issue completion.

### Data / API / format contract

- GitHub body metadata uses the keys and exact formats defined above; hashes are lowercase hexadecimal SHA-256 values.
- Contract comment payload encoding is UTF-8. The version header is excluded from the payload byte count and payload SHA.
- New profile hook options `--issue` and `--capability` are defined by the [Project Profile and Agent Context Specification](project-profile-spec.md).
- GitHub operations MUST use structured JSON and argument arrays. User payloads MUST NOT be interpolated into shell command strings.

## Error and boundary behavior

| Condition | Required behavior |
|---|---|
| Empty, oversized, invalid UTF-8, NUL-containing, or obvious-secret contract | Reject before remote pointer change; preserve any existing mirror. |
| API 403/404, wrong Issue/PR, altered body, byte-count/SHA mismatch | Fail closed; do not report verified and leave prior local bytes unchanged. |
| Same-SHA publish retry after comment creation | Reuse the matching comment and retry pointer update without creating a duplicate. |
| Different contract SHA without `--supersede` | Reject without changing the current pointer or prior comment. |
| Existing mirror differs from verified remote contract without `--replace-stale` | Reject without changing either existing local bytes or remote state. |
| Issue body changed during pointer update | Stop and report conflict; preserve unrelated body sections. |
| PR head changes after review publication | Report stale review and fail handoff until review is regenerated. |
| Required Check absent, pending, or failed | Fail handoff; never convert the state to success. |
| Rendered Implementation Contract comment exceeds 65,536 characters | Reject locally before remote mutation and preserve the local mirror. |
| Draft PR metadata check | Keep Ready-only evidence pending; do not report handoff success. |
| Merge finalization called before merged PR and closed Issue | Fail without changing phase labels. |
| Merge finalization finds a phase label other than `phase:review` | Fail without changing any labels. |
| Temporary file creation or API operation fails | Clean up temporary payloads and preserve existing mirror/pointer state where the operation has not completed. |

## Quality attributes

### Security and privacy

Contract and review payloads are sent only to the named repository Issue/PR. Logs MUST omit payloads and credentials. CI PR jobs are read-only and MUST NOT expose secrets to untrusted code. Local hooks are trusted shell configuration and are not a security sandbox.

### Performance and scalability

Contract verification is bounded to one named comment and a maximum 64 KiB raw payload; publish also enforces the 65,536-character rendered-comment limit. Context generation MUST avoid comment-list APIs and full body output.

### Accessibility and usability

N/A — these are command-line and CI interfaces with no visual interaction surface.

### Portability and platform behavior

The workflow and wrappers MUST cover the platforms listed under CI and the CLI semantics MUST remain consistent across Bash and PowerShell wrappers. An unrun platform is reported as unverified.

## Compatibility and versioning

New CLI commands MUST be additive. Existing commands and Schema 1 behavior remain compatible. Existing Schema 2 Targets without `requirements` retain their prior compatibility behavior. The contract-comment format is versioned as `agent-contract:v1`; unknown versions MUST fail closed.

## Acceptance traceability

| Requirement / acceptance criterion | Specification section | Verification |
|---|---|---|
| Exact contract bytes, comment identity, idempotence, superseding, restore, and mirror preservation | [Contract distribution](#contract-distribution) | `test_contract_distribution.py` with fake GitHub/API responses |
| Checklist, PR head, draft, close reference, phase, and Required Check validation | [Self-review and delivery](#self-review-and-delivery) | `test_review_delivery.py` |
| Generic rationale, Quick component selection, Target gates, and Schema 1/old Schema 2 compatibility | [Project Profile and Agent Context Specification](project-profile-spec.md) | `test_project_profile.py` |
| CI trust boundary, starter profile, metadata checks, and template preservation | [CI and trust boundary](#ci-and-trust-boundary) | Workflow inspection and CI matrix execution |
| Cross-platform command behavior and user-visible failures | [Portability and platform behavior](#portability-and-platform-behavior) | Bash and PowerShell wrapper checks; unavailable systems reported unverified |
