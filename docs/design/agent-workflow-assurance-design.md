<!-- agent-doc-type: design -->
<!-- agent-doc-schema: 2 -->
# Agent Workflow Assurance Design

- Status: Approved
- Owning Issue: #5
- Related specification: [Agent Workflow Assurance Specification](../specs/agent-workflow-assurance-spec.md)

## Overview

The Python agent CLI coordinates Issue-scoped contract and PR review artifacts through narrow GitHub API calls, while a verified local mirror supports recovery. Delivery checks read current Issue, PR, and Required Check state. Repository CI validates code and PR evidence with read-only permissions. The design keeps authoritative public payloads in the single named GitHub comment and prevents stale or partial local state from being reported as verified.

## Context and goals

Issue #5 adds assurance to the existing phase workflow. The architecture must make contract and review evidence independently retrievable, preserve exact source bytes, fail closed on API or concurrency uncertainty, and distinguish implementation handoff from merged Issue completion. Profile Target and Issue-document routing remain within the existing project-profile ownership boundary and are specified by the [Project Profile Specification](../specs/project-profile-spec.md).

## Requirements traceability

| Requirement/spec section | Design consequence |
|---|---|
| [Contract distribution](../specs/agent-workflow-assurance-spec.md#contract-distribution) | A contract codec validates raw bytes before any pointer update; a one-comment GitHub adapter verifies by ID; a local mirror writer uses atomic replacement. |
| [Self-review and delivery](../specs/agent-workflow-assurance-spec.md#self-review-and-delivery) | PR self-review publication validates the effective checklist and HEAD before writing a comment pointer; handoff re-reads live PR, Issue, and check state. |
| [CI and trust boundary](../specs/agent-workflow-assurance-spec.md#ci-and-trust-boundary) | PR CI runs tests and read-only metadata checks without secrets or untrusted configured hooks. |
| [Hook selection and ordering](../specs/project-profile-spec.md#hook-selection-and-ordering) | The existing project-profile owner gates Target commands and preserves project/component/target order. |
| [Context routing output](../specs/project-profile-spec.md#context-routing-output) | Context output adds only validated owner paths and planned-owner paths; it does not fetch or inline document contents. |

## Architecture overview

The existing `scripts/agent/agent_tool.py` remains the sole behavior owner for CLI operations. It coordinates three state boundaries: GitHub Issue/PR metadata and named comments, local per-Issue recovery state, and CI status checks. GitHub CLI/API calls use argument arrays and structured JSON; payload bytes are held in temporary files rather than interpolated into shell strings.

```text
User contract / self-review
        |
        v
agent_tool.py -- validate bytes, checklist, and current HEAD
        |                           |
        v                           v
one named GitHub comment       Issue-scoped local mirror
        |                           |
        +------ verified pointers --+
                    |
                    v
      delivery-check reads Issue + PR + checks
                    |
                    v
       read-only PR metadata/evidence CI job
```

The Issue and PR bodies hold compact pointers. The named comment holds each complete payload. The local mirror is a recovery copy, not the public source of truth after a pointer has been published.

## Architecture invariants

- Contract hashes and byte counts cover the exact UTF-8 payload, excluding only the version header; no newline normalization is allowed.
- Every remote verification fetches one comment by its recorded ID. Normal context generation never fetches all comments or full payloads.
- A failed identity, length, SHA, stale-replacement, or ownership check leaves the pre-existing local mirror unchanged.
- Same-Issue/same-SHA publish is idempotent. Superseding creates a new immutable comment only after explicit `--supersede`.
- Issue pointer changes preserve unrelated sections and require immediate pre-read plus readback. Concurrent Issue body edits stop the operation.
- PR self-review describes one exact HEAD. Any new commit makes the prior review stale.
- Delivery success is derived from live state, including configured Required Checks. Unconfigured, pending, failed, or absent CI is not success.
- CI reads untrusted PR code and metadata without secrets/write credentials and does not run arbitrary hooks from the PR's project profile.
- Temporary payloads are cleaned up on normal success and handled failure paths; payload and token contents are never logged.

## Component responsibilities

| Component/module | Responsibility | Must not own |
|---|---|---|
| `agent_tool.py` contract codec | Validate payload size, UTF-8, forbidden bytes, header, SHA, and pointer metadata. | GitHub API transport or normalization of source text. |
| `agent_tool.py` GitHub adapter | Read or write a specific Issue/PR pointer and one named comment through `gh`. | Listing unrelated comments, silently resolving conflicts, or printing payloads. |
| `.agent-state/issues/N/` | Store the verified payload, SHA record, and explicit SHA-named stale backup. | Authoritative remote approval after a pointer exists. |
| Self-review and delivery commands | Validate checklist/head metadata and derive stage state from live GitHub metadata and checks. | Treating submitted claims as independent evidence or making merge decisions. |
| `.github/workflows/template-ci.yml` | Run the platform matrix and read-only PR metadata/evidence validation. | Secrets, write tokens, or execution of untrusted profile hooks. |
| Project Profile and Context command path | Select components, parse Document impact, and gate Target hooks. | Contract publishing or PR delivery policy. |

## Data and control flow

### Contract publish and restore

1. Read the source bytes without decoding/re-encoding for hash calculation; reject empty, oversized, invalid UTF-8, NUL, or obvious-secret input.
2. Build the versioned comment header from the Issue number, raw payload byte count, and raw payload SHA-256.
3. For an existing matching Issue/SHA, reuse its one named comment. A changed SHA requires explicit superseding and creates a separate immutable comment.
4. Retrieve the created/reused comment by ID and verify repository/Issue association, header, byte count, and SHA.
5. Re-read the Issue body, replace only its contract metadata section, write the update, and read it back. If this fails, retain the comment for same-SHA recovery.
6. Restore reads the comment ID from the Issue pointer and fetches only that comment. Validate the entire header and association before writing any local file.
7. If the existing mirror differs, stop unless `--replace-stale` is explicit. Save the old bytes under their SHA before atomically replacing the mirror.

### Self-review and delivery

1. Checklist extraction prefers the canonical reviewer block. Without one, a narrow heading matcher accepts `Reviewer Checklist`, an optional numeric prefix, and an optional ASCII or Japanese parenthetical qualifier; unrelated headings do not match. Self-review publication first runs `validate-self-review` against the current HEAD and effective checklist.
2. Publish the full review as one PR conversation comment. Verify the named comment's PR, SHA, checklist, and Reviewed HEAD before changing the PR pointer.
3. Validation fetches the named comment only. It compares the PR's current head to Reviewed HEAD and returns stale when they differ.
4. Handoff reads repository identity, PR draft/open state, `Closes #N`, Issue phase, current PR head, review pointer, verification/untested fields, and every configured Required Check. It validates the project profile schema with initialization not required, preserving the checked-in template starter. App-specific requirements match only that app's check-run; source-unrestricted and legacy contexts match a passing check-run by name or a successful commit status. Check-run conclusions `success`, `skipped`, and `neutral` pass; commit statuses require `success`.
5. Merged delivery additionally requires a merged PR and closed Issue. Finalization removes only stale `phase:review`; any other phase label stops cleanup without mutation. Repeating cleanup after review-phase removal succeeds without mutation.

### Context and verification composition

The context path fetches Issue number, state, labels, URL, and body once, resolves `closed` from Issue state before label-based phase routing, then resolves affected components from the canonical section and only explicit same-repository paths in `## Document impact`. Closed Issues report `phase=closed` with no workflow path. Existing owners are displayed as `document_owner=<repo-relative-path>`; future paths are displayed as `planned_owner=<repo-relative-path>`. A URL that cannot be proven to identify an in-scope path in the current repository produces a diagnostic and is not emitted as an owner.

The verification path selects Issue-affected components for Quick checks and all components by default for Final checks. For each target, it checks OS, normalized architecture, required PATH tools, then explicitly supplied capabilities. The first mismatch skips the target command and records it as unverified; all other eligible hooks retain their configured sequential order.

## Ownership and lifecycle

Each command invocation owns its temporary JSON and payload files and removes them in a `finally` cleanup path. The per-Issue directory owns the local contract and SHA record. Same-Issue publish, restore, pointer update, and supersede operations run serially; a conflict stops instead of racing. No daemon, shared cache, or external database is introduced.

## Error handling and recovery

| Failure point | Result / propagation | Cleanup | Retry / recovery |
|---|---|---|---|
| Invalid local payload | Reject before remote mutation. | Remove temporary files; existing mirror remains unchanged. | Correct the source and retry. |
| Comment creation succeeded but Issue pointer update failed | Report partial publication; retain the immutable comment. | Clean temporary files. | Retry the same Issue/SHA and reuse the named comment. |
| API returns 403/404 or comment identity/hash validation fails | Fail closed; do not change local mirror or claim verified state. | Clean temporary files. | Restore access or correct the authoritative pointer. |
| Mirror conflicts with verified remote content | Leave existing mirror bytes unchanged unless replacement was explicit. | Clean temporary files. | Review the SHA backup and use `--replace-stale` deliberately. |
| Concurrent Issue body edit | Stop pointer write or report failed readback; never claim atomic CAS. | Clean temporary files. | Re-read and retry after edits are serialized. |
| PR head advances after review | Mark published review stale; fail handoff. | No local review state is promoted. | Revalidate and publish a new review for the new head. |
| Required Check missing, pending, or failing | Delivery check fails; no success state is emitted. | No labels are changed. | Configure or rerun the required check. |
| Finalization called before merged/closed state | Fail without changing labels. | No cleanup needed. | Retry after GitHub reports merged and closed. |

## Concurrency and async model

Each command is a one-shot serial operation. The same Issue's publishing and pointer operations MUST NOT run concurrently. GitHub does not offer a strict compare-and-swap for Issue bodies, so immediate pre-read/readback is the limit and concurrent Issue-body edits are unsupported. CI jobs may run concurrently because they are read-only and do not mutate shared state.

## Quality attributes and operations

### Security

GitHub authentication remains inside the configured `gh` credential boundary. CLI arguments carry file paths and identifiers, not payload strings. CI metadata checks use read-only permissions and do not execute untrusted PR-configured hooks.

### Performance and resource strategy

The codec caps raw payloads at 64 KiB and checks the rendered comment against GitHub's 65,536-character limit before posting. The version header counts toward that limit, so the effective raw maximum is slightly lower for ASCII-heavy content. The Issue and PR body remain compact; context generation emits only paths and diagnostics.

### Observability, diagnostics, and supportability

Commands report operation stage, Issue/PR ID, SHA, and actionable failure class without payload text or credentials. Skipped targets and unavailable platforms remain explicitly unverified in review evidence and handoff reports.

### Platform / backend / deployment considerations

Bash and PowerShell wrappers dispatch to the same Python CLI semantics. GitHub API behavior is accessed through `gh`; unavailable platforms or Required Checks are never inferred as successful.

## Compatibility and migration

All new commands are additive. Existing save behavior remains available for local-only legacy mirrors. Schema 1 behavior and existing Schema 2 profiles without Target requirements remain intact. No issue history is rewritten, and superseding comments preserve the previous approved source.

## Verification strategy

| Risk/invariant | Verification method |
|---|---|
| Raw byte preservation, pointer identity, retries, restore conflict, and unchanged mirrors | Fake GitHub/API unit tests with CRLF, final-newline, and adversarial responses. |
| Current review checklist and HEAD | Fake PR metadata tests for stale, wrong SHA, wrong PR, and valid publication. |
| Handoff and merge completion | Required Check, draft, Close reference, phase, merged/closed, and repeat-finalization test matrix. |
| Target non-execution and Issue Quick scope | Project-profile tests assert zero command calls on every mismatch and preserve Schema 1/2 behavior. |
| CI trust and platform gaps | Workflow permission review plus real matrix results; unavailable systems remain unverified. |
| Starter/downstream document protection | Documentation validator and template-update preservation tests. |

## Alternatives considered

### Put full contract or self-review text in Issue/PR bodies

- Advantages: one fewer comment lookup.
- Rejected because: large bodies are harder to preserve and validate; bodies remain compact pointers while named comments are independently hashed.

### Fetch all comments to locate the current contract or review

- Advantages: does not require a pointer.
- Rejected because: it expands context and permissions unnecessarily and makes identity/version selection ambiguous.

### Store canonical payloads in an external database or Gist

- Advantages: centralized storage independent of Issues.
- Rejected because: it adds an external dependency and another authorization boundary; the owning Issue/PR comment is the approved source.

## Risks and open follow-ups

- GitHub cannot provide strict compare-and-swap for Issue body changes; callers must serialize edits and stop on a changed-body readback.
- A configured Required Check must exist and report against the current PR head before handoff can pass.
- Windows and macOS CI results are required for platform verification; local execution on another OS is not a substitute.
