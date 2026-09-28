<!-- agent-doc-type: design -->
<!-- agent-doc-schema: 2 -->
# <Feature / Architecture> Design

- Status: Draft
- Owning Issue: #<issue>
- Related specification: TBD

## Overview

Explain the architecture mental model, subsystem boundary, key invariants, important lifecycle/failure constraints, and related authoritative spec/design documents. Keep this concise and link related documents with meaningful relative Markdown links. This overview is explanatory; detailed sections remain authoritative.

## Context and goals

Summarize the approved problem, consumers, system boundary, and architecture goals. Do not redefine public requirements here.

## Requirements traceability

| Requirement/spec section | Design consequence |
|---|---|
| ... | ... |

Trace material requirements to the design decisions that realize them.

## Architecture overview

Describe the subsystem boundary, mental model, dependencies, and major components. Paths and symbols may identify architectural seams or canonical locations of invariants; do not make an exhaustive code inventory.

```text
<optional architecture diagram>
```

## Architecture invariants

List the durable properties that implementations and refactors must preserve.

## Component responsibilities

| Component/module | Responsibility | Must not own |
|---|---|---|
| ... | ... | ... |

State dependency direction and ownership boundaries.

## Data and control flow

Describe important normal and failure flows, ordering, validation/transformation, and dependency interactions.

### Persistence and cache

State source of truth, ownership, invalidation, consistency, transaction/atomicity, and migration where relevant. Otherwise give a concrete N/A reason.

## Ownership and lifecycle

For resources with meaningful lifetimes, state creation and steady-state owner, destruction initiator/order, outstanding callback/subscription/task handling, post-destroy behavior, use-after-destroy prevention, and release guarantees. Otherwise give a concrete N/A reason.

## Error handling and recovery

| Failure point | Result / propagation | Cleanup | Retry / recovery |
|---|---|---|---|
| initialization or partial construction | ... | ... | ... |
| malformed input or dependency failure | ... | ... | ... |
| cancellation, timeout, shutdown | ... | ... | ... |

Consider repeated calls, reentrancy, owner destruction during work, rollback, and cleanup.

## Concurrency and async model

State thread/executor/actor boundaries, synchronization, ordering, cancellation, reentrancy, and thread-affinity constraints. Use `N/A — <concrete reason>` only when these concerns do not apply.

## Quality attributes and operations

Consider security boundaries, resource/performance/scalability limits, diagnostics, supportability, and platform/deployment differences. For commercially operated systems, cover logging, telemetry/metrics, failure visibility, rollout/feature flags, rollback, and data migration where relevant. Use concrete N/A reasons when irrelevant.

### Security

...

### Performance and resource strategy

...

### Observability, diagnostics, and supportability

...

### Platform / backend / deployment considerations

...

## Compatibility and migration

State migration and rollout steps, compatibility constraints, deprecation, rollback, and forward/backward behavior.

## Verification strategy

Map risks and invariants to tests or runtime evidence. Durable design records the strategy; actual run results belong in status/evidence.

| Risk/invariant | Verification method |
|---|---|
| ... | ... |

## Alternatives considered

### <Alternative>

- Advantages:
- Rejected because:

## Risks and open follow-ups

List residual risks and follow-up Issues. Material unresolved architecture decisions block approval.
