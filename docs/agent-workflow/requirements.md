# Requirements phase

Read this file for a new repository-changing request without an owning Issue or while the Issue is in `phase:requirements`.

## Goal

Turn the request into a bounded, testable problem statement without starting implementation.

## Required actions

1. Locate the owning Issue/PR using only the minimal lookup needed.
2. If none exists, create an Issue immediately with `phase:requirements` before broad planning or repository edits.
3. If version milestones are enabled, run `ensure-version-milestone.*`.
4. After Issue ownership is established, inspect only relevant code/docs.
5. Record Background, Objective, Functional requirements, Non-goals, Constraints, Acceptance criteria, Unresolved questions, and Document impact in the Issue.
6. Classify the change as one or more of: public/observable contract, durable architecture, implementation-only, bug fix, or verification-only.
7. Do not silently resolve ambiguities that materially affect API, compatibility, architecture, supported platforms, security, or scope.
8. Use `needs-user-decision` for a blocking user/maintainer decision and `blocked` for an external/technical blocker.

## Affected components

When the project profile has multiple schema-2 components, list every affected component in the Issue using the canonical section:

```markdown
## Affected components

- `desktop`
- `server`
```

Use component IDs from `.agent/project.json`; do not use an `all` token. A single-component schema-2 project may omit the section, in which case its only component is selected. Schema-1 projects retain root-project scope. The [Project Profile and Agent Context Specification](../specs/project-profile-spec.md) owns parsing and error behavior.

Once the Issue identifies the affected components, run `agent-context.* <issue>` before broad source or document inspection. Read only the selected conditional application profiles and the relevant specification/design/status owners it routes.

## Document impact

Before leaving requirements, state the disposition of each document responsibility in the Issue:

```markdown
## Document impact

- Specification:
  - update existing: [<owner>](<link>)
  - create: `<future relative path>`
  - or none — <concrete reason>
- Design:
  - update existing: [<owner>](<link>)
  - create: `<future relative path>`
  - or none — <concrete reason>
- Status/evidence:
  - update/create: <target>
  - or none — <concrete reason>
```

Link existing owners. A future file cannot be linked until it exists; record its exact relative path. Do not use an unspecified “docs update” as the impact statement.

## Specification impact gate

If requested behavior changes a public or observable contract, the design phase MUST create/update the relevant specification before implementation. Use the [specification standard](../standards/specification.md) and [documentation synchronization standard](../standards/documentation-sync.md).

Acceptance criteria should be observable. Architecture-specific obligations belong in design and the Reviewer Checklist.

## Completion

Requirements are ready for design when scope/non-goals are clear, acceptance criteria are testable, Document impact is explicit, and no unresolved question blocks design.

Transition to `phase:design`.
