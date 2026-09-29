# Documentation synchronization standard

Use this responsibility chain:

```text
requirements -> specs -> design -> code/tests -> status/evidence
```

Do not introduce a parallel authority source.

## Document routing

| Information | Owner |
|---|---|
| Observable product contract | specification |
| Durable architecture and invariants | design |
| Task-only decisions and review discussion | Issue/PR |
| Implementation mechanism | source code, comments, and tests |
| Actual progress and verification result | status/evidence |

Every durable rule has exactly one semantic owner. Other documents link to that owner instead of restating the rule. New or split durable documents must be linked from the corresponding ownership index.

## Change impact

| Change | Specs | Design | Status/evidence |
|---|---|---|---|
| externally observable product or tool behavior/API/protocol | update first | if architecture changes | update current state |
| durable architecture/ownership/threading | only if contract changes | update first | update current state |
| implementation-only refactor | no | only if durable design changes | usually no |
| bug fix conforming to existing contract | no | only if prior design was wrong/incomplete | update if tracked gap closes |
| verification-only change | no | test strategy only if durable | update verification state if useful |

A document update is required because its responsibility changed, not merely because code changed.

Before implementation, identify the owning specification and design or record a concrete reason that either is unnecessary. New material public-contract or architecture decisions discovered during implementation return to requirements/design.

## Precedence and current state

Shared/portable specifications take precedence over narrower product, platform, or profile specifications for shared semantics. A narrower owner may restrict capabilities or add product-specific observable behavior but may not redefine shared rules.

Specifications and designs describe current required behavior and architecture. Keep completed Issue/PR history, old implementation attempts, superseded workarounds, commit SHAs, one-off verification results, and investigation transcripts in task history or evidence rather than durable docs. Preserve a rejected alternative only when its rationale remains useful.

Never rewrite historical evidence into `docs/status/`. Keep status concise and current.

## Navigation and progressive disclosure

Ownership indexes tell readers which document owns a semantic area. Indexes use meaningful clickable relative Markdown links and do not restate rules. Large repositories may use nested indexes.

Navigational Markdown references must be clickable; a code-form path alone is insufficient. Schema-2 validation rejects broken relative `.md` targets. External HTTP/HTTPS links are not network-checked.

Durable documents provide progressive disclosure: ownership index, concise human-readable Overview, then normative/architecture detail, relevant failure and quality topics, and verification references.
