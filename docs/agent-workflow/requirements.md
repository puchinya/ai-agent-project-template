# Requirements phase

Read this file for a new repository-changing request without an owning Issue or while the Issue is in `phase:requirements`.

## Goal

Turn the request into a bounded, testable problem statement without starting implementation.

## Required actions

1. Locate the owning Issue/PR using only the minimal lookup needed.
2. If none exists, create an Issue immediately with `phase:requirements` before broad planning or repository edits.
3. If version milestones are enabled, run `ensure-version-milestone.*`.
4. After Issue ownership is established, inspect only relevant code/docs.
5. Separate:
   - Background
   - Objective
   - Functional requirements
   - Non-goals
   - Constraints
   - Acceptance criteria
   - Unresolved questions
   - Document impact
6. Classify the change as one or more of:
   - public/observable contract
   - durable architecture
   - implementation-only
   - bug fix
   - verification-only
7. Do not silently resolve ambiguities that materially affect API, compatibility, architecture, supported platforms, security, or scope.
8. Use `needs-user-decision` for a blocking user/maintainer decision and `blocked` for an external/technical blocker.

## Specification impact gate

If the requested behavior changes a public or observable contract, the design phase MUST create/update the relevant `docs/specs/` document before implementation.

Acceptance criteria should be observable. Architecture-specific obligations belong in design and the Reviewer Checklist.

## Completion

Requirements are ready for design when scope/non-goals are clear, acceptance criteria are testable, and no unresolved question blocks design.

Transition to `phase:design`.
