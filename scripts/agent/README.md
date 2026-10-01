# Agent helper scripts

The `.sh` and `.ps1` files are thin wrappers over `agent_tool.py`.

Shared logic lives in one place to avoid shell/PowerShell behavior drift.

Project-specific commands are data in `.agent/project.json` hooks rather than hard-coded workflow text.

Schema-2 profiles separate components, technology stacks, application types, and build/run targets. `init-project` defaults to the `root` component and `generic` application type; `--application-type` and `--target` accept comma-separated values. Targets created by `init-project` use `runnable_on: ["any"]` until a narrower host is recorded. Explicit stack IDs are accepted so repositories can use custom technologies.

`agent-context <issue>` prints a compact routing manifest. For schema-2 multi-component projects, the Issue must contain an `## Affected components` section with one `- \`component-id\`` item per component. The manifest lists selected conditional application profiles without inlining their contents.

`run-hook verify_quick` and `run-hook verify_final` run global hooks, selected component hooks, then target hooks supported on the current runtime host. Repeat `--component <id>` to select components; omit it to select all. `verify_quick --issue <number>` selects only components listed in that Issue's `## Affected components` and cannot be combined with `--component`. `verify_final` defaults to every component. Target requirements gate by OS, normalized architecture, installed tools, and explicitly supplied `--capability <id>` values. A skipped target never runs and remains unverified.

## Contract and review delivery

Implementation Contracts are kept as exact-byte local mirrors and a single top-level comment on their owning Issue. The Issue body stores only the comment ID, SHA-256, and `approved` state. Commands:

```text
save-implementation-contract <issue> [path]
publish-implementation-contract <issue> [--source path] [--supersede]
restore-implementation-contract <issue> [--replace-stale]
verify-implementation-contract <issue>
```

Publish reads and writes one known comment ID at a time. Contract text is sent in a temporary JSON file, bounded to 64 KiB raw, checked for UTF-8, NUL bytes, and obvious credentials, then verified by bytes and SHA-256. Before any POST, the rendered comment including its version header must also fit within GitHub's 65,536-character limit; the header makes the effective raw maximum slightly lower for ASCII-heavy payloads. Oversized rendered comments are rejected without remote mutation or mirror changes. Do not paste the full text into normal Issue/PR context or fetch comment lists.

```text
publish-self-review <issue> --pr <number>
validate-public-review <issue> --pr <number> [--head <40-char-sha>]
delivery-check <issue> --pr <number> --stage handoff|merged
finalize-merged-issue <issue> --pr <number>
```

The PR body points to one public Self-review comment. Handoff requires an open, ready PR, `Closes #<issue>`, `phase:review`, complete Verification and Untested fields, valid public review for the PR HEAD, and configured green Required Checks. App-specific checks must come from the configured app; unrestricted and legacy contexts can pass from a matching successful check-run or commit status. `success`, `skipped`, and `neutral` check-run conclusions pass; commit statuses require `success`. A `generic` affected component also requires a concrete Generic profile rationale. After merge and Issue closure, finalization removes only stale `phase:review`, fails without mutation on any other phase label, and is idempotent after cleanup.

## Document validation

`validate-docs` reads the required documentation schema from `.agent/template-files.json`. If an older manifest has no `documentation_schema_version`, schema 1 remains the default. Schema 2 requires the schema-2 headings and checks local relative Markdown links in durable specifications/designs. Large-document and missing-index reports are warnings.

## Template updates

`update-template --check` does not write files. It reports managed-file status and any durable spec/design documents that need the source template schema. Exit code `2` means managed-file conflicts; exit code `3` means no managed conflict remains but semantic documentation migration is required.

Apply mode keeps the existing three-way safe file update and never rewrites project-specific specs/design/status. After exit code `3`, migrate those documents manually in the same template-update Issue/PR, rerun the updater until it returns `0`, then run `validate-docs` and project verification. There is no automatic semantic migration helper.

See the [template update standard](../../docs/standards/template-update.md) for the complete workflow.
