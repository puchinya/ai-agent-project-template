# Design document standard

A design document defines **how approved requirements/specifications are realized** through durable internal architecture. One durable documentation system must serve both people and agents.

## Normative role

Design is authoritative for durable internal decisions such as:

- module/component responsibilities and dependency direction;
- ownership, lifetime, construction/destruction order, and cleanup;
- data, control, and failure flow;
- concurrency, async, threading, cancellation, and reentrancy;
- persistence, cache, consistency, and synchronization;
- error representation, propagation, and recovery;
- security boundaries and platform/backend separation;
- resource, performance, and scalability strategy;
- operational supportability and migration approach;
- test architecture and verification strategy.

Local implementation details that are obvious from code do not need durable design documentation.

## Progressive disclosure and human readability

Organize each durable design so readers can move from an ownership index to a concise overview, then to architecture, lifecycle and failure details, quality concerns, and verification references.

Every schema-2 design begins substantive content with a concise `## Overview`. It explains the architecture mental model, subsystem boundary, key invariants, important lifecycle/failure constraints, and related authoritative spec/design documents. It is explanatory; detailed sections remain authoritative.

## Design durability test

> If an internal refactor preserves the same architecture, a sentence that must change solely because a file/function/class name changed is normally too implementation-specific for durable design.

Design must be decision-complete for material architecture. An implementer should not need to invent a major ownership, dependency, concurrency, persistence, compatibility, or failure-handling decision while coding.

It must distinguish facts, approved decisions, alternatives, and remaining risks.

## Semantic ownership and splitting

Every durable rule has exactly one semantic owner. Other documents link to that owner instead of restating the rule.

Split a design when sections have independent semantic owners, can change independently, have different subsystem owners, are consumed separately, or repeatedly cause unrelated work to edit the same document. Size alone is not a reason to split.

Paths and symbols may anchor an ownership boundary, architectural seam, required ordering, or canonical location of an invariant. They must not become an exhaustive file/function/class inventory.

## Required qualities

For each design, cover relevant architecture boundaries, invariants, component responsibilities, dependency direction, data/control/failure flow, ownership/lifecycle, concurrency, error handling, persistence/cache, security, resource/performance strategy, observability, compatibility, platform differences, verification, and rejected alternatives. Do not omit a material topic silently. Use `N/A — <concrete reason>` only when genuinely irrelevant.

For relevant operations, consider initialization failure, partial construction, malformed input, dependency failure, cancellation, timeout, repeated calls, reentrancy, owner destruction during work, shutdown/cleanup, and retry/recovery.

For resources with meaningful lifetimes, state creation and steady-state owners, destruction initiator/order, outstanding callback/task handling, post-destroy behavior, use-after-destroy prevention, and release guarantees.

Operational quality includes logging, diagnostics, telemetry/metrics, failure visibility, supportability, rollout/feature flags, rollback, and data migration when applicable. Pure compile-time or library-only features may use a reasoned N/A.

## Required sections by document schema

Documents containing `<!-- agent-doc-type: design -->` and no schema marker use schema 1 for backward compatibility. Their required headings remain:

- `## Context and goals`
- `## Requirements traceability`
- `## Architecture overview`
- `## Component responsibilities`
- `## Data and control flow`
- `## Ownership and lifecycle`
- `## Error handling and recovery`
- `## Concurrency and async model`
- `## Compatibility and migration`
- `## Verification strategy`
- `## Alternatives considered`
- `## Risks and open follow-ups`

Schema-2 designs use these required top-level headings:

- `## Overview`
- `## Context and goals`
- `## Requirements traceability`
- `## Architecture overview`
- `## Architecture invariants`
- `## Component responsibilities`
- `## Data and control flow`
- `## Ownership and lifecycle`
- `## Error handling and recovery`
- `## Concurrency and async model`
- `## Quality attributes and operations`
- `## Compatibility and migration`
- `## Verification strategy`
- `## Alternatives considered`
- `## Risks and open follow-ups`

Quality-attribute prompts should consider security, performance/resource limits, observability/diagnostics/supportability, and platform/backend/deployment differences. The validator requires the top-level `## Quality attributes and operations` heading; subheadings guide authors.

## Design rules

- Public behavior must point back to its specification/requirements rather than being invented here.
- Dependencies must have a direction; avoid “components call each other as needed”.
- Ownership and cleanup must be explicit for resources with lifetimes.
- Concurrency must identify thread/actor/executor boundaries, ordering, cancellation, reentrancy, and synchronization where relevant.
- Errors must identify origin, representation, propagation, effect, and retry/recovery where relevant.
- Performance decisions must include the constraint that justifies added complexity.
- Rejected alternatives must state why they were rejected.
- Verification must map risky design decisions to tests or runtime evidence.
- Navigational Markdown references must be clickable; schema-2 validation rejects broken relative `.md` file targets.
- Durable documents describe current state, not Issue/PR chronology or one-off verification results.

## Prohibited patterns

- Repeating the specification in different words.
- A class/file inventory without responsibility boundaries.
- “Use best practices” in place of a decision.
- Deferring all difficult decisions to implementation.
- Describing only the happy path.
- Treating a diagram as sufficient without textual invariants.
- Adding issue history, old workarounds, commit SHAs, or test-run history merely for chronology.
