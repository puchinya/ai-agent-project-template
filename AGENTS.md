# AGENTS.md

This file is the repository-wide source of truth for AI coding agents. Provider-specific files must route here instead of duplicating shared rules.

## Project profile bootstrap

Before repository-changing work, confirm `.agent/project.json` exists and contains `"initialized": true`.

If not, run:

- macOS/Linux: `scripts/agent/init-project.sh`
- Windows PowerShell: `.\scripts\agent\init-project.ps1`

Then read `docs/agents/project.md`.

Technology-specific commands, cleanup rules, and verification commands MUST come from `.agent/project.json` hooks or `docs/agents/project.md`, not from guessed framework defaults.

## Mandatory task bootstrap

Before agent-local planning, TODO creation, broad repository investigation, or editing repository-controlled files, classify the requested end result.

For every repository-changing task:

1. If the user identified an Issue or Pull Request, use it. Otherwise perform only the minimal GitHub lookup needed to find an existing owner.
2. If no Issue owns the request, read `docs/agent-workflow/requirements.md`, create an Issue with `phase:requirements`, and only then continue normal planning or detailed investigation.
3. If version milestones are enabled in `.agent/project.json`, run `scripts/agent/ensure-version-milestone.* <issue-number>`.
4. Determine the active phase from Issue labels / PR state and read only that phase workflow document.
5. Only after Issue ownership and the required workflow entry step may broad planning, detailed investigation, design, or repository editing begin.

Research-only work does not require an Issue unless requested. If research becomes approved repository-changing work, run this bootstrap before continuing the change.

Use `gh` for GitHub operations and `git` for local branch/staging/commit/push operations.

For multiline GitHub Markdown, use a body file when the command supports it. Never encode intended line breaks as literal `\n`.

## Workflow routing

| State | Workflow |
|---|---|
| new request / `phase:requirements` | `docs/agent-workflow/requirements.md` |
| `phase:design` | `docs/agent-workflow/design.md` |
| `phase:ready` / `phase:implementation` | `docs/agent-workflow/implementation.md` |
| `phase:review` / open PR | `docs/agent-workflow/review.md` |

Read `checkpoint.md` only for pause/resume and `evidence.md` only when handling evidence.

## Documentation authority

| Source | Authority |
|---|---|
| `docs/specs/` | normative public / observable contract |
| `docs/design/` | durable internal architecture |
| source code | current implementation |
| tests | executable implementation evidence |
| `docs/status/` | concise current implementation / gap / verification state |
| `docs/agents/` | project and technology execution rules |
| `docs/agent-workflow/` | Issue phase workflow |
| `docs/standards/` | documentation quality rules |

Dependency direction:

```text
specs -> design -> code -> status
```

Never change a specification merely to match an implementation bug. Never use status as authority for desired behavior or architecture.

When a change affects an observable contract, update/approve the specification before implementation. When it introduces a durable architectural decision, update/approve the design before implementation.

Use:
- `docs/standards/specification.md`
- `docs/standards/design.md`
- `docs/standards/documentation-sync.md`

New durable documents should start from `docs/templates/`.

## Input modes

Repository-changing work has two modes:

- **Direct request**: requirements -> design -> implementation -> review.
- **Supplied Implementation Contract**: compressed decision-complete handoff, not a workflow bypass. Associate it with the owning Issue and save an exact local mirror using `save-implementation-contract.*`.

Approved repository specs/design/Issue decisions override a conflicting contract.

## Context invariant

Keep an Issue-scoped working set: owning Issue/PR, active phase workflow, relevant spec/design/status sections, target symbols/tests/dependencies, project profile, and current relevant diff.

Prefer bounded search/ranges/diffs. Do not scan all docs, repeatedly reread unchanged large files, or paste full logs into active context. Put retained raw logs under `.agent-state/issues/<issue>/logs/`.

## Branch and technology hooks

For source-code changes, use:

```text
scripts/agent/start-feature-branch.* <issue> <short-description>
```

The helper owns feature branch naming and invokes the configured `branch_switch` hook only after an actual branch switch.

Example: a Rust profile may configure `cargo clean`. This is project policy, not a universal workflow rule.

Run project hooks through:

```text
scripts/agent/run-hook.* verify_quick
scripts/agent/run-hook.* verify_final
```

Do not silently replace configured hooks with ad-hoc alternatives.

## Verification and document gate

Use focused checks during iteration. Once stable, run the configured final gate.

Before PR delivery:

- project-required verification passes;
- `scripts/agent/validate-docs.*` passes;
- acceptance criteria are satisfied or explicitly blocked;
- the effective Reviewer Checklist has item-level results against the committed HEAD.

## Delivery gate

Implementation is not complete at edit, test, commit, or push.

Before implementation-phase completion is reported:

- repository changes are committed;
- `validate-self-review.* <issue>` passes;
- branch is pushed;
- PR exists and contains `Closes #<issue>`;
- Issue is in `phase:review`;
- `docs/agent-workflow/review.md` has been entered.

Overall Issue completion remains merge-gated.

## Communication

Follow the user's language unless the repository defines another communication policy.


## Template update tasks

When the task is to update this template or apply a newer version of this template to another project, read `docs/standards/template-update.md`.

Do not overwrite project-specific files such as `.agent/project.json`, `docs/agents/project.md`, source files, or project-specific specs/design/status documents during template synchronization.
