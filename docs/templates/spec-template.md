<!-- agent-doc-type: specification -->
<!-- agent-doc-schema: 2 -->
# <Feature / Contract> Specification

- Status: Draft
- Owning Issue: #<issue>
- Related design: TBD

## Overview

Explain the consumer/user mental model, key guarantees, important limitations, and related authoritative documents. Keep this concise and link related documents with meaningful relative Markdown links. This overview is explanatory; the detailed contract below is authoritative.

## Purpose

State the user/system outcome this contract guarantees and who consumes it.

## Scope

### In scope

- ...

### Out of scope

- ...

## Terminology

| Term | Meaning |
|---|---|
| ... | ... |

## Semantic ownership

Name the semantic area this document owns. Link to other owners instead of repeating their rules.

## Normative requirements

- The system MUST ...
- The system MUST NOT ...
- The system SHOULD ...

Use RFC-style terms only for conformance requirements, not implementation preferences.

## Observable behavior

Describe inputs, outputs, externally visible state transitions, ordering, and deterministic/nondeterministic behavior.

### State model

If stateful, define states and allowed transitions.

### Data / API / format contract

Define schemas, units, ranges, defaults, optionality, and encoding where relevant.

## Error and boundary behavior

| Condition | Required behavior |
|---|---|
| invalid input | ... |
| boundary value | ... |
| dependency failure | ... |
| cancellation or timeout | ... |

Include partial-work and recovery outcomes when consumers can observe them.

## Quality attributes

Consider each topic. Use `N/A — <concrete reason>` only when it is genuinely irrelevant.

### Security and privacy

Describe contractual security/privacy constraints, data sensitivity, and user control, or state a concrete reason for N/A.

### Performance and scalability

State only externally meaningful guarantees and limits. Internal optimization belongs in design.

### Accessibility and usability

For user-facing behavior, state relevant accessibility and usability requirements. For non-user-facing behavior, give a concrete N/A reason.

### Portability and platform behavior

State supported platforms and any observable platform differences, or give a concrete N/A reason.

## Compatibility and versioning

State stable and extensible behavior, unknown-value handling, backward/forward compatibility, migration behavior, deprecation, breaking changes, platform support, and versioning where relevant. Give a concrete N/A reason for irrelevant topics.

## Acceptance traceability

| Requirement / acceptance criterion | Specification section | Verification |
|---|---|---|
| ... | ... | ... |

Trace each important requirement to its verification method. Stable IDs are useful for shared or versioned rules; they are not required for every small feature.
