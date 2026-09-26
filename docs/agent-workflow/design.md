# Design phase

Read only while the Issue is in `phase:design`.

## Goal

Make approved behavior and material architecture decision-complete enough that implementation does not invent major requirements or architecture.

## Document impact first

Apply `docs/standards/documentation-sync.md`.

- observable/public contract changed -> update `docs/specs/`
- durable architecture changed -> update `docs/design/`
- new nontrivial feature -> normally both are expected unless one is demonstrably unnecessary

Use the templates and standards. Run `validate-docs.*` before approving design.

## Required design topics

Cover relevant topics and explicitly use `N/A` with reason for template sections that do not apply:

- public behavior traceability
- component/module responsibilities
- dependency direction
- data/control/failure flow
- ownership/lifecycle
- concurrency/async/threading
- errors/recovery
- persistence/cache/consistency
- platform/backend boundaries
- compatibility/migration
- performance/resource constraints
- verification strategy
- alternatives considered/rejected

## Reviewer Checklist approval gate

Before `phase:ready`, the Issue must contain an effective task-specific:

```markdown
## Reviewer Checklist
- [ ] ...
```

Checklist items must cover task-specific risks that acceptance criteria alone do not make safe to infer.

For a supplied Implementation Contract, its valid checklist may provide part/all of the effective checklist. Repository-specific supplemental items may remain in the Issue.

A material requirement discovered later is not silently added during implementation; return to requirements/design.

## Approval gate

Do not begin nontrivial implementation until requirements, required specs/design, and Reviewer Checklist are approved by the user or responsible maintainer.

After approval:

1. keep the Issue body aligned with approved requirements/design summary;
2. validate docs;
3. replace `phase:design` with `phase:ready`.
