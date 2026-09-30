# Agent helper scripts

The `.sh` and `.ps1` files are thin wrappers over `agent_tool.py`.

Shared logic lives in one place to avoid shell/PowerShell behavior drift.

Project-specific commands are data in `.agent/project.json` hooks rather than hard-coded workflow text.

Schema-2 profiles separate components, technology stacks, application types, and build/run targets. `init-project` defaults to the `root` component and `generic` application type; `--application-type` and `--target` accept comma-separated values. Targets created by `init-project` use `runnable_on: ["any"]` until a narrower host is recorded. Explicit stack IDs are accepted so repositories can use custom technologies.

`agent-context <issue>` prints a compact routing manifest. For schema-2 multi-component projects, the Issue must contain an `## Affected components` section with one `- \`component-id\`` item per component. The manifest lists selected conditional application profiles without inlining their contents.

`run-hook verify_quick` and `run-hook verify_final` run global hooks, selected component hooks, then target hooks supported on the current runtime host. Repeat `--component <id>` to select components; omit it to select all. Host-incompatible target checks are reported as `SKIPPED_TARGET_VERIFICATION` and remain unverified.

## Document validation

`validate-docs` reads the required documentation schema from `.agent/template-files.json`. If an older manifest has no `documentation_schema_version`, schema 1 remains the default. Schema 2 requires the schema-2 headings and checks local relative Markdown links in durable specifications/designs. Large-document and missing-index reports are warnings.

## Template updates

`update-template --check` does not write files. It reports managed-file status and any durable spec/design documents that need the source template schema. Exit code `2` means managed-file conflicts; exit code `3` means no managed conflict remains but semantic documentation migration is required.

Apply mode keeps the existing three-way safe file update and never rewrites project-specific specs/design/status. After exit code `3`, migrate those documents manually in the same template-update Issue/PR, rerun the updater until it returns `0`, then run `validate-docs` and project verification. There is no automatic semantic migration helper.

See the [template update standard](../../docs/standards/template-update.md) for the complete workflow.
