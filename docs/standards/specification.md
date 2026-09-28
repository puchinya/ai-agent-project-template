# Specification standard

A specification defines **what the system guarantees**, not how the current implementation happens to work. One durable documentation system must serve both people and agents.

## Normative role

A specification is authoritative for externally observable behavior, public APIs, file/protocol formats, user-visible state transitions, cross-module contracts, compatibility guarantees, and required failure behavior.

Implementation details belong in [the design documents](../design/README.md).

## Progressive disclosure and human readability

Organize each durable specification so readers can move from an ownership index to a concise overview, then to the normative contract, edge cases, quality attributes, and verification references.

The target reader is a competent engineer who is unfamiliar with the subsystem. The document must explain the consumer mental model, purpose, guarantees, limitations, risks, and invariants without requiring an initial code search. It must also be precise enough that an independent implementer does not invent a material product decision.

Every schema-2 specification begins substantive content with a concise `## Overview`. It explains the consumer/user mental model, key guarantees, important limitations, and related authoritative documents. It is explanatory; detailed normative sections remain authoritative.

## Specification test

> If the implementation were completely replaced but consumers still had to observe the same rule, the rule belongs in the specification.

Describe externally observable outcomes. Do not specify an internal mechanism merely because it explains the current implementation.

## Semantic ownership

Every durable rule has exactly one semantic owner. Other documents link to the owner instead of restating the rule. Ownership indexes identify the document responsible for a semantic area and do not duplicate its rules.

Split a document when sections have independent semantic owners, can change independently, have different subsystem owners, are consumed separately, or repeatedly cause unrelated work to edit the same document. Size alone is not a reason to split.

## Required qualities

A good specification is:

- unambiguous enough that two implementations can be judged against it;
- testable through observable outcomes;
- explicit about purpose, consumers, scope, and non-goals;
- explicit about inputs, outputs, state transitions, ordering, boundaries, and failure behavior where relevant;
- explicit about compatibility, versioning, and portability where relevant;
- traceable to owning requirements / Issue acceptance criteria;
- independent from incidental class names or algorithms unless they are themselves contractual.

Use RFC-style keywords deliberately:

- **MUST / MUST NOT** — required for conformance.
- **SHOULD / SHOULD NOT** — expected unless a documented reason applies.
- **MAY** — optional behavior.

Do not use those keywords for implementation preferences.

## Quality attributes

Consider security/privacy, externally meaningful performance and scalability, accessibility/usability for user-facing software, compatibility/versioning, and portability/platform behavior. Do not omit a material concern silently. When a topic is genuinely irrelevant, state `N/A — <concrete reason>`.

## Compatibility and product/profile precedence

Where relevant, distinguish stable and extensible behavior, unknown values, deprecation, breaking changes, and forward/backward compatibility.

Shared/portable behavior takes precedence over a product, platform, or profile specification. A narrower specification may restrict supported capabilities or add product-specific observable behavior; it must not redefine shared semantics. When shared semantics conflict, the upstream owner wins.

## Current-state-only content

Specifications describe the current required state. Do not retain completed Issue/PR chronology, old attempts, superseded workarounds, commit SHAs, one-off verification results, investigation transcripts, or obsolete hypotheses merely for history. Keep task chronology in Issue/PR/Git history and actual verification state in status/evidence.

Preserve a rejected alternative only when its rationale remains useful to prevent an unsafe or incompatible design from returning.

## Conformance, verification, and evidence

Keep these roles distinct:

- specification: required conformance and observable outcomes;
- design: how this implementation plans to verify risky contracts and invariants;
- tests: executable checks;
- status/evidence: what was actually verified, on which environment and HEAD.

Trace each important requirement to its design consequence and verification method. Stable requirement IDs are recommended for shared, versioned, protocol, or ABI rules; they are not required for every small feature.

## Cross-document navigation

Markdown references used for navigation must be clickable links with meaningful labels. Prefer relative repository links. Use heading fragments when stable. A code-form path may accompany a link when the exact path matters, but must not be the only navigation. Do not use absolute local paths. Schema-2 validation rejects broken relative `.md` file targets; HTTP/HTTPS links are not network-checked.

## Required sections by document schema

Documents containing `<!-- agent-doc-type: specification -->` and no schema marker use schema 1 for backward compatibility. Their required headings remain:

- `## Purpose`
- `## Scope`
- `## Terminology`
- `## Normative requirements`
- `## Observable behavior`
- `## Error and boundary behavior`
- `## Compatibility and versioning`
- `## Acceptance traceability`

Schema-2 specifications use these required top-level headings:

- `## Overview`
- `## Purpose`
- `## Scope`
- `## Terminology`
- `## Semantic ownership`
- `## Normative requirements`
- `## Observable behavior`
- `## Error and boundary behavior`
- `## Quality attributes`
- `## Compatibility and versioning`
- `## Acceptance traceability`

Quality-attribute prompts should consider `### Security and privacy`, `### Performance and scalability`, `### Accessibility and usability`, and `### Portability and platform behavior`. The validator requires the top-level `## Quality attributes` heading; these subheadings guide authors.

## Prohibited patterns

- Treating source code as the normative contract.
- Writing only happy-path prose.
- Mixing internal module decomposition into a public contract without need.
- Replacing a requirement with “works like current implementation”.
- Leaving material unresolved questions in an approved normative document.
- Changing the specification merely to make a defect appear conformant.
- Duplicating a normative rule across documents instead of linking to its owner.

## Review questions

- Can behavior be tested without knowing the implementation?
- Is the consumer mental model clear before the detail?
- Are valid/invalid inputs, ordering, boundaries, and state transitions clear?
- Are failure, security, accessibility, performance, compatibility, and platform concerns covered or explicitly N/A with a reason?
- Is each rule traceable to exactly one semantic owner?
- Are navigation links clickable and valid?
- Is every MUST actually necessary?
- Does the design realize this specification rather than redefine it?
