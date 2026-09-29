<!-- agent-doc-type: specification -->
<!-- agent-doc-schema: 2 -->
# Agent Tooling Specification

- Status: Approved
- Template source: [ai-agent-project-template Issue #1](https://github.com/puchinya/ai-agent-project-template/issues/1)
- Related design: N/A — this contract does not introduce a durable architecture change.

## Overview

This specification defines the stable command-line behavior used to validate durable documentation and update projects from the template. It gives maintainers and agents predictable validation results, migration reports, and file-preservation guarantees. The [documentation synchronization standard](../standards/documentation-sync.md) defines document authority; the [template update standard](../standards/template-update.md) explains the workflow around these commands.

## Purpose

Guarantee consistent, locally observable behavior for `validate-docs` and `update-template` so maintainers and downstream agents can decide whether documentation is valid, whether migration is required, and whether a template update can proceed safely.

## Scope

### In scope

- Required documentation schema interpretation by `validate-docs` and `update-template`.
- Validation results, migration report fields, command exit codes, and project-specific document preservation.
- Template distribution of this shared specification as the single explicitly managed specification under `docs/specs/`.

### Out of scope

- The internal parsing, validation, or safe three-way update algorithms.
- Authoring quality policy beyond what affects command results; see the [specification standard](../standards/specification.md) and [design standard](../standards/design.md).
- Project-specific specifications, designs, status documents, and downstream repository changes.

## Terminology

| Term | Meaning |
|---|---|
| Required schema | Minimum documentation schema declared by the source template manifest. |
| Durable document | A specification or design Markdown file under `docs/specs/` or `docs/design/`, excluding ownership README files. |
| Migration required | A durable document has a valid parsed schema lower than the source template's required schema. |
| Managed conflict | A managed destination cannot be safely updated from the source template. |

## Semantic ownership

This document is the single normative owner of externally observable behavior for `validate-docs` and `update-template`. Standards may describe how to use or maintain these commands but must link here for their stable CLI contract. Source code and tests implement and verify this specification; they do not replace it as the authority.

## Normative requirements

- `validate-docs` MUST read `documentation_schema_version` from the template manifest. If the field is absent, it MUST use schema 1. Supported required schemas are 1 and 2; an invalid manifest value MUST be reported as a validation error.
- `validate-docs` MUST validate durable specification and design documents against the required schema and the headings required by each document type.
- A schema-2 document MUST have valid schema metadata, all required schema-2 headings, and no broken relative Markdown `.md` links. External links are not network-checked.
- Schema-2 size and ownership-index findings MUST remain warnings and MUST NOT make validation fail.
- `update-template` MUST classify a document as requiring migration only when its parsed schema is valid and lower than the source template's required schema. A missing schema marker parses as schema 1. Malformed, duplicate, or unsupported markers MUST NOT be reported as ordinary schema-1 migrations; `validate-docs` reports them as document errors.
- A schema-2 heading or link defect MUST NOT cause migration exit code 3. `validate-docs` is responsible for reporting those defects.
- `update-template --check` MUST NOT write files. Apply mode MAY update managed template files and template state, but MUST NOT rewrite project-specific durable specifications, designs, or status documents.
- `update-template` MUST report conflicts and migrations in either mode. A managed conflict MUST take precedence over migration when selecting the exit code.
- No command covered by this specification may perform network validation of Markdown links or automatic semantic migration of project-specific documents.

## Observable behavior

`validate-docs` exits 0 when documents meet the required schema and validation rules; warnings may be printed without changing that result. On success it prints `docs_validation=pass checked=<count> warnings=<count> required_schema=<schema>`. Validation errors are printed with an `error:` prefix to standard error and produce exit code 1.

`update-template` reports the selected mode and managed-file counts, then emits the migration report fields defined below. It applies the safe managed-file update before reporting outstanding migrations in apply mode. Migration detection is independent of other schema-2 content validation.

### State model

The update result is determined in this order:

1. If a managed conflict exists, exit 2.
2. Otherwise, if at least one valid lower-schema durable document exists, exit 3.
3. Otherwise, exit 0.

Document validity is a separate `validate-docs` result. A schema-2 defect does not create a migration state.

### Data / API / format contract

Every `update-template` report MUST include these stable lines, in this order:

```text
documentation_schema_required=<schema>
documentation_migration_required=<count>
MIGRATION_REQUIRED <repository-relative-path>
```

There is one `MIGRATION_REQUIRED` line per lower-schema document, with paths in deterministic ascending order. When no documents require migration, the count is zero and there are no migration path lines. Conflict lines use the `CONFLICT <path>` form and are reported before the command exits.

## Error and boundary behavior

| Condition | Required behavior |
|---|---|
| Required schema is missing from the source manifest | Use schema 1 for compatibility. |
| Required schema is malformed or unsupported | Report an error and exit 1. |
| A specification or design file lacks its matching document-type marker | `validate-docs` reports a validation error. |
| Document has no schema marker and schema 2 is required | Classify as schema 1 for migration reporting; `validate-docs` reports that schema 2 is required. |
| Document has malformed, duplicate, or unsupported schema markers | Do not classify it as a migration; `validate-docs` reports a schema error. |
| Schema-2 document is missing a required heading or has a broken local `.md` link | Do not classify it as a migration; `validate-docs` exits 1. |
| Managed conflict and migration both exist | Report both; exit 2. |
| Migration exists with no managed conflict | Exit 3. |
| Neither conflict nor migration exists | Exit 0. |
| `update-template --check` is selected | Do not modify managed files, project documents, or template state. |

## Quality attributes

These commands are local developer tools. Their stable output is intended for maintainers and agent workflows, not end users.

### Security and privacy

Validation and template-update behavior MUST remain local and MUST NOT transmit document contents. Link validation MUST NOT fetch external resources.

### Performance and scalability

No timing guarantee is defined. Work is limited to the repository documentation tree and the managed files named by the source manifest.

### Accessibility and usability

The commands MUST provide readable text output and stable machine-detectable field prefixes. No graphical or assistive-technology interface is part of this contract.

### Portability and platform behavior

The contract applies to supported repository environments using the provided platform wrappers. No platform-specific difference in exit-code precedence or report fields is permitted.

## Compatibility and versioning

Schema 1 remains supported when the source manifest omits `documentation_schema_version` or explicitly requires 1. A schema-1 document remains valid when schema 1 is required; schema-2 documents may be used with either minimum. A schema-2 requirement makes schema-1 documents migration-required and causes `validate-docs` to report them as invalid until manually updated. No automatic content migration is provided. Template version remains 0.4.0 for this contract.

## Acceptance traceability

| Requirement / acceptance criterion | Specification section | Verification |
|---|---|---|
| Migration detection uses only valid lower-schema documents | Normative requirements; State model | Migration-versus-validation regression tests |
| Schema-2 heading and link defects fail validation without becoming migrations | Normative requirements; Error and boundary behavior | Focused `validate-docs` tests |
| Exit codes and migration report remain stable in check and apply modes | State model; Data / API / format contract | Update-template output and precedence tests |
| Project-specific durable documents are never overwritten by template apply | Normative requirements | Apply-mode preservation test |
| Documentation requirements and local link rules remain enforceable | Normative requirements | `validate-docs` and repository documentation validation |
