# Template update and downstream synchronization standard

This template is intended to evolve while already-running projects keep their own project-specific choices.

## Managed vs project-specific files

Template-managed files are listed in `.agent/template-files.json`. They are safe to update from a newer template version when they have not been locally changed.

Project-specific files are intentionally not overwritten by template updates:

- `.agent/project.json`
- `docs/agents/project.md`
- source code and tests
- Issue/PR-specific evidence
- project-specific specifications, designs, and status documents

If a project wants to customize a template-managed file, it should either:

1. move the local rule into a project-specific file and keep the template file generic; or
2. accept that future `update-template` runs may report a conflict for that file.

## Safe update model

`update-template` uses a three-way safety check:

- previous template hash stored in `.agent/template-state.json`;
- current downstream file hash;
- new template file hash from `.agent/template-files.json`.

The updater applies a file automatically only when the downstream file still matches the previously recorded template hash, or when the file is missing.

If both the template and the downstream file changed, the updater does not overwrite. It writes an `.incoming-template` file and reports a conflict.

## First adoption in an existing project

For an existing project that did not start from this template:

```bash
./scripts/agent/update-template.sh --source ../ai-agent-project-template --adopt
```

`--adopt` records existing matching files as the current baseline and copies missing managed files. Conflicting files are left untouched and accompanied by `.incoming-template` files for manual merge.

## Documentation schema migration during template update

The stable observable CLI contract for `validate-docs` and `update-template`, including report fields and exit codes, is owned by the [Agent Tooling Specification](../specs/agent-tooling-spec.md).

The source template manifest owns `documentation_schema_version`. The field is a requirement of the adopted template, not a project-specific setting; do not move it into `.agent/project.json`.

When the source manifest requires schema 2, the downstream repository must migrate all durable specification and design documents to schema 2 within the same template-update Issue/PR. Project-specific specifications, designs, and status documents remain non-managed and are never automatically rewritten by the updater.

`update-template --check` makes no changes. It reports the required schema, migration count, and each `MIGRATION_REQUIRED <path>`. Exit code `2` means there is a managed-file conflict. Otherwise, exit code `3` means project documents still need migration; exit code `0` means neither condition remains.

Apply mode retains the three-way safe managed-file update. It may apply managed files and write template state, then report outstanding project-document migrations and return `3`. This is intentional. Managed conflicts retain precedence and return `2`; if both conditions exist, both are reported. The updater never modifies project-specific durable documents.

After exit code `3`, read the new specification and design standards, review each listed document semantically, preserve one owner per rule, remove history from durable docs, add a human-readable Overview, cover relevant failure/lifecycle/quality topics, update ownership indexes, and fix navigational Markdown links. Do not blindly add headings or split files based only on size. Rerun the updater and require exit code `0`, then run `validate-docs`, the configured final verification, self-review, and the PR review workflow. A template-update PR is incomplete while migrations remain.

A source manifest with no `documentation_schema_version` is treated as schema 1 for backward compatibility. Values other than supported integer versions are errors.

## Updating after the template improves

```bash
git checkout -b chore/update-agent-template
./scripts/agent/update-template.sh --source ../ai-agent-project-template
./scripts/agent/validate-docs.sh
./scripts/agent/run-hook.sh verify_final
```

If the updater returns `3`, complete the semantic document migration in this same Issue/PR and rerun the updater. Then inspect conflicts, commit, and open a PR.

## Rule

A template update must be reviewable as a normal repository change. Do not silently update agent workflow files directly on the default branch.
