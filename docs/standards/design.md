# Design document standard

A design document defines **how approved requirements/specifications are realized** through durable internal architecture.

## Normative role

Design is authoritative for durable internal decisions such as:

- module/component responsibilities;
- dependency direction and abstraction boundaries;
- ownership and lifecycle;
- data and event flow;
- concurrency / async / threading;
- persistence, cache, and synchronization;
- error propagation and recovery;
- platform/backend separation;
- major performance strategy;
- migration approach;
- test architecture.

Local implementation details that are obvious from code do not need durable design documentation.

## Required qualities

A good design document is decision-complete for material architecture. An implementer should not need to invent a major ownership, dependency, concurrency, persistence, compatibility, or failure-handling decision while coding.

It must distinguish facts, approved decisions, alternatives, and remaining risks.

## Required sections for template-managed designs

Documents containing `<!-- agent-doc-type: design -->` must contain:

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

Use `N/A` with a concrete reason when a topic truly does not apply; do not silently omit a material topic.

## Design rules

- Public behavior must point back to specs/requirements rather than being invented here.
- Dependencies must have a direction; avoid “components call each other as needed”.
- Ownership and cleanup must be explicit for resources with lifetimes.
- Concurrency must identify thread/actor/executor boundaries and synchronization.
- Errors must identify origin, propagation, user/system effect, retry/recovery where relevant.
- Performance decisions must include the constraint that justifies added complexity.
- Rejected alternatives must state why they were rejected.
- Verification must map risky design decisions to tests or runtime evidence.

## Prohibited patterns

- Repeating the specification in different words.
- A class/file inventory without responsibility boundaries.
- “Use best practices” in place of a decision.
- Deferring all difficult decisions to implementation.
- Describing only the happy path.
- Treating a diagram as sufficient without textual invariants.
