# Agent helper scripts

The `.sh` and `.ps1` files are thin wrappers over `agent_tool.py`.

Shared logic lives in one place to avoid shell/PowerShell behavior drift.

Project-specific commands are data in `.agent/project.json` hooks rather than hard-coded workflow text.

## Document validation

`validate-docs` reads the required documentation schema from `.agent/template-files.json`. If an older manifest has no `documentation_schema_version`, schema 1 remains the default. Schema 2 requires the schema-2 headings and checks local relative Markdown links in durable specifications/designs. Large-document and missing-index reports are warnings.

## Template updates

`update-template --check` does not write files. It reports managed-file status and any durable spec/design documents that need the source template schema. Exit code `2` means managed-file conflicts; exit code `3` means no managed conflict remains but semantic documentation migration is required.

Apply mode keeps the existing three-way safe file update and never rewrites project-specific specs/design/status. After exit code `3`, migrate those documents manually in the same template-update Issue/PR, rerun the updater until it returns `0`, then run `validate-docs` and project verification. There is no automatic semantic migration helper.

See the [template update standard](../../docs/standards/template-update.md) for the complete workflow.
