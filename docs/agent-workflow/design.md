# Design phase

Read only while the Issue is in `phase:design`.

Before broad design research, confirm the Issue's affected components and run `agent-context.* <issue>`. Read the selected conditional application profiles and only the relevant specification/design/status owners; do not load all standards or ownership documents by default.

## Goal

Make approved behavior and material architecture decision-complete enough that implementation does not invent major requirements or architecture.

## Document Architecture Gate

Apply the [documentation synchronization standard](../standards/documentation-sync.md), [specification standard](../standards/specification.md), and [design standard](../standards/design.md).

Before `phase:ready`, verify that:

1. each changed observable rule has exactly one specification owner;
2. each material durable architecture decision has exactly one design owner;
3. task-only decisions remain in the Issue/PR;
4. rediscoverable implementation detail remains in code/comments/tests;
5. actual progress and verification results remain in status/evidence;
6. new/split durable documents are linked from an ownership index;
7. navigational Markdown references are clickable;
8. schema-2 commercial-quality topics are covered or explicitly N/A with a concrete reason;
9. the Reviewer Checklist covers task-relevant failure, boundaries, ownership/lifecycle, cleanup, concurrency/reentrancy/cancellation, compatibility, security, performance/resources, platform differences, and operational/supportability risks.

Update the relevant [specification owners](../specs/README.md) for observable contract changes and [design owners](../design/README.md) for durable architecture changes. A new nontrivial feature normally needs both unless one is demonstrably unnecessary; record a concrete reason for either omission. Do not make a durable design mandatory for a trivial bug fix that creates no durable architecture decision.

Use the [specification template](../templates/spec-template.md) and [design template](../templates/design-template.md). Run `validate-docs.*` before approving design.

## Required design topics

Cover relevant topics and use `N/A — <concrete reason>` only when a template topic truly does not apply:

- public behavior traceability;
- component/module responsibilities and dependency direction;
- architecture invariants and data/control/failure flow;
- ownership, lifetime, and cleanup;
- concurrency, async/thread boundaries, cancellation, and reentrancy;
- errors and recovery;
- persistence, cache, and consistency;
- platform/backend boundaries;
- compatibility and migration;
- security, performance, and resource constraints;
- observability and supportability;
- verification strategy and alternatives considered/rejected.

## Reviewer Checklist approval gate

Before `phase:ready`, the Issue must contain an effective task-specific checklist:

```markdown
## Reviewer Checklist
- [ ] ...
```

Checklist items cover risks that acceptance criteria alone do not make safe to infer. A valid checklist in a supplied Implementation Contract may provide part or all of the effective checklist; repository-specific supplemental items may remain in the Issue.

A material requirement discovered later is not silently added during implementation; return to requirements/design.

## Target and assurance design topics

For schema-2 targets, specify optional `requirements.architectures`, `requirements.tools`, and `requirements.capabilities` separately from `runnable_on`. Define host/architecture/tool/capability skip behavior and which capabilities must be explicitly supplied. Do not infer application type from stack or host. For contract publication, review evidence, and CI trust boundaries, route to the dedicated [assurance design](../design/agent-workflow-assurance-design.md) and [assurance specification](../specs/agent-workflow-assurance-spec.md) rather than duplicating their protocols here.

## Approval gate

Do not begin nontrivial implementation until requirements, required specs/design, and the Reviewer Checklist are approved by the user or responsible maintainer.

After approval:

1. keep the Issue body aligned with the approved requirements/design summary;
2. validate docs;
3. replace `phase:design` with `phase:ready`.
