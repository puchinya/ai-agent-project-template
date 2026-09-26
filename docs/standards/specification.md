# Specification standard

A specification defines **what the system guarantees**, not how the current implementation happens to work.

## Normative role

A specification is authoritative for externally observable behavior, public APIs, file/protocol formats, user-visible state transitions, cross-module contracts, compatibility guarantees, and required failure behavior.

Implementation details belong in `docs/design/`.

## Required qualities

A good specification is:

- unambiguous enough that two implementations can be judged against it;
- testable through observable outcomes;
- explicit about scope and non-goals;
- explicit about boundary and failure behavior;
- explicit about compatibility and versioning when relevant;
- traceable to owning requirements / Issue acceptance criteria;
- independent from incidental class names or algorithms unless they are themselves contractual.

Use RFC-style keywords deliberately:

- **MUST / MUST NOT** — required for conformance.
- **SHOULD / SHOULD NOT** — expected unless a documented reason applies.
- **MAY** — optional behavior.

Do not use those keywords for implementation preferences.

## Required sections for template-managed specifications

Documents containing `<!-- agent-doc-type: specification -->` must contain:

- `## Purpose`
- `## Scope`
- `## Terminology`
- `## Normative requirements`
- `## Observable behavior`
- `## Error and boundary behavior`
- `## Compatibility and versioning`
- `## Acceptance traceability`

Additional sections are encouraged for data formats, state machines, security/privacy, performance guarantees, and examples when relevant.

## Prohibited patterns

- Treating source code as the normative contract.
- Writing only happy-path prose.
- Mixing internal module decomposition into a public contract without need.
- Replacing a requirement with “works like current implementation”.
- Leaving material unresolved questions in an approved normative document.
- Changing the spec merely to make a defect appear conformant.

## Review questions

- Can behavior be tested without knowing the implementation?
- Are valid/invalid inputs and state transitions clear?
- Are failure semantics defined?
- Are compatibility consequences explicit?
- Is every MUST actually necessary?
- Does the design implement this specification rather than redefine it?
