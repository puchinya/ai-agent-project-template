<!-- agent-doc-type: design -->
# <Feature / Architecture> Design

- Status: Draft
- Owning Issue: #<issue>
- Related specification: `<path>`

## Context and goals

Summarize the approved problem and architecture goals. Do not redefine public requirements here.

## Requirements traceability

| Requirement/spec section | Design decision |
|---|---|
| ... | ... |

## Architecture overview

Describe the system boundary, dependency direction, key invariants, and major components.

```text
<optional architecture diagram>
```

## Component responsibilities

| Component/module | Responsibility | Must not own |
|---|---|---|
| ... | ... | ... |

## Data and control flow

Describe important normal flows and where validation/transformation occurs.

### Failure flow

Describe how dependency failures, partial work, cancellation, retries, or rollback propagate.

## Ownership and lifecycle

State resource ownership, creation/destruction, subscription cleanup, persistence lifetime, and shutdown behavior.

Use `N/A` only with a concrete reason.

## Error handling and recovery

| Failure source | Representation | Propagation | Recovery/user effect |
|---|---|---|---|
| ... | ... | ... | ... |

## Concurrency and async model

State thread/executor/actor boundaries, synchronization, cancellation, ordering, reentrancy, and thread-affinity constraints.

Use `N/A` only with a concrete reason.

## Persistence and cache

State source of truth, cache invalidation, consistency, transaction/atomicity, and schema migration where relevant.

## Platform / backend considerations

Describe shared vs platform-specific behavior and abstraction boundaries.

## Performance and resource strategy

State measurable constraints that justify caching, batching, virtualization, pooling, or other complexity.

## Compatibility and migration

State migration steps, rollout order, backward compatibility, and deprecation handling.

## Verification strategy

Map risks and invariants to unit/integration/e2e/runtime verification.

| Risk/invariant | Verification |
|---|---|
| ... | ... |

## Alternatives considered

### <Alternative>

- Advantages:
- Rejected because:

## Risks and open follow-ups

List residual risks and follow-up Issues. Material unresolved architecture decisions block approval.
