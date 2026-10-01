# AGENTS.md

This file is the repository-wide source of truth for AI coding agents. Provider-specific files must route here instead of duplicating shared rules.

## Project profile bootstrap

Before repository-changing work, confirm `.agent/project.json` exists and contains `"initialized": true`.

If not, run:

- macOS/Linux: `scripts/agent/init-project.sh`
- Windows PowerShell: `.\scripts\agent\init-project.ps1`

Use `.agent/project.json` as the machine-readable project authority and `scripts/agent/agent-context.* <issue>` for normal agent routing. `docs/agents/project.md` is an optional generated human-readable summary and does not need to be read by default.

Technology-specific commands, cleanup rules, and verification commands MUST come from validated `.agent/project.json` hooks and the configured project runners, not from the generated Markdown summary or guessed framework defaults.

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
- **Supplied Implementation Contract**: compressed decision-complete handoff, not a workflow bypass. Associate it with the owning Issue, save the exact local bytes using `save-implementation-contract.*`, then publish/restore/verify through the matching contract commands when the Issue pointer is available. Keep the approved source in one top-level Issue comment; never copy its full text into the Issue body.

Approved repository specs/design/Issue decisions override a conflicting contract.

## Context invariant

Keep an Issue-scoped working set in this order:

1. owning Issue/PR;
2. active phase workflow;
3. affected components from the Issue and project profile;
4. conditional application profiles selected by those components;
5. relevant specification/design/status owners linked from the Issue;
6. target symbols, tests, and dependencies;
7. current relevant diff.

Use `scripts/agent/agent-context.* <issue>` to produce a compact routing manifest. Read only the selected application profiles and linked owners; do not load every standard, specification, design, or application profile by default. The manifest routes readers and does not replace the linked documents.

`agent-context` may print `document_owner` and `planned_owner` paths from the Issue's `## Document impact`. Only direct Markdown files under `docs/specs/`, `docs/design/`, and `docs/status/` in the same repository are accepted; ambiguous or foreign links are diagnostics. It never fetches contract comments or expands their text.

Closed Issues report `phase=closed` from Issue state with no active workflow path, even if a stale phase label remains.

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

Schema-2 profiles run project, selected component, and compatible target hooks in that order. Repeat `--component <id>` to limit a verification hook to specific components; without it, all components are selected. `verify_quick --issue <number>` derives components only from that Issue's `## Affected components` and cannot be combined with `--component`. `verify_final` defaults to every component. Optional target requirements gate by OS, architecture, installed tools, then explicitly supplied `--capability` values; skips do not run hooks and remain unverified. Schema-1 profiles keep their existing hook behavior.

Do not silently replace configured hooks with ad-hoc alternatives.

## Verification and document gate

Use focused checks during iteration. Once stable, run the configured final gate.

Before PR delivery:

- project-required verification passes;
- `scripts/agent/validate-docs.*` passes;
- acceptance criteria are satisfied or explicitly blocked;
- the effective Reviewer Checklist has item-level results against the committed HEAD.
- for a generic affected component, the PR has a concrete `Generic profile rationale`.

## Delivery gate

Implementation is not complete at edit, test, commit, or push.

Before implementation-phase completion is reported:

- repository changes are committed;
- `validate-self-review.* <issue>` passes;
- branch is pushed;
- PR exists and contains `Closes #<issue>`;
- the public Self-review comment and PR pointer validate against the exact Checklist and HEAD;
- `delivery-check.* <issue> --pr <pr> --stage handoff` confirms Required Checks are configured and green;
- Issue is in `phase:review`;
- `docs/agent-workflow/review.md` has been entered.

Create the PR as Draft, move the Issue to `phase:review`, publish the validated Self-review, then mark the PR ready after the PR body is complete. Overall Issue completion remains merge-gated. After merge and Issue closure, use `finalize-merged-issue.*`; it removes only stale `phase:review`, fails without mutation if another `phase:*` label remains, and is idempotent after cleanup.

Hooks are arbitrary shell commands configured in the trusted `.agent/project.json`. They are not sandboxed. CI must validate PR metadata and project-independent template fixtures in read-only jobs; never run PR-supplied hooks with secrets or write permissions.

## Communication

Follow the user's language unless the repository defines another communication policy.


## Template update tasks

When the task is to update this template or apply a newer version of this template to another project, read `docs/standards/template-update.md`.

Do not overwrite project-specific files such as `.agent/project.json`, `docs/agents/project.md`, source files, or project-specific specs/design/status documents during template synchronization.
