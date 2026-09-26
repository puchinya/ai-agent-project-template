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

## Updating after the template improves

```bash
git checkout -b chore/update-agent-template
./scripts/agent/update-template.sh --source ../ai-agent-project-template
./scripts/agent/validate-docs.sh
./scripts/agent/run-hook.sh verify_final
```

Then inspect conflicts, commit, and open a PR.

## Rule

A template update must be reviewable as a normal repository change. Do not silently update agent workflow files directly on the default branch.
