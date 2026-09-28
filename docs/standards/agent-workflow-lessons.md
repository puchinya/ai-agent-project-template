# Agent workflow lessons folded into this template

This document records practices that were added because they prevent recurring failures in AI-agent-driven development.

## Issue ownership before planning

Agents often start their own planning protocol before repository workflow. This template requires Issue ownership before broad investigation, task lists, or edits.

## Active phase document only

Agents lose context by reading every workflow document. This template routes by Issue phase and instructs agents to read only the active phase document.

## Specification and design are different artifacts

A common failure mode is writing implementation notes as a specification, or repeating public behavior as a design. This template separates:

- `docs/specs/`: observable contract;
- `docs/design/`: durable internal architecture;
- `docs/status/`: current implementation state.

## Reviewer Checklist fixed before implementation

Late-added review criteria make implementation appear complete even when the original risk was never checked. This template fixes the effective Reviewer Checklist before implementation.

## Reviewed-HEAD gate

Self-review becomes stale after any new commit. This template requires `Reviewed-HEAD` to match the current commit and a clean worktree.

## Implementation Contract exact mirror

Compressed instructions are useful, but paraphrasing them causes drift. This template stores the exact contract with SHA-256 and reuses it after context compaction or handoff.

## Template-managed updates

Without an updater, improvements to the workflow do not reach active projects. This template now includes managed-file manifests and `update-template` to apply safe updates and surface conflicts.

## GitHub Markdown transport

Literal `\n` in GitHub bodies caused broken Issues/PRs. This template requires body files for multiline Markdown.

## Logs and evidence do not belong in status docs

`docs/status/` is for concise current state. Raw logs, screenshots, and transient evidence belong in `.agent-state/` or small curated `docs/issues/` evidence.

## Technology-specific policy belongs in the project profile

Rules like Rust `cargo clean` are valuable in some repositories and harmful in others. This template moves such behavior to `.agent/project.json` hooks.

## Semantic ownership beats catch-all documents

One durable rule has one semantic owner. Split documents when ownership and change boundaries differ, not just because a file is large. Ownership indexes let readers find the right document without repeating its rules.

## Durable documents describe current state

Specifications and designs explain current required behavior and architecture. Completed Issue history, superseded workarounds, implementation transcripts, and one-off verification results belong in Issue/PR history or evidence.

## Code inventories are not architecture

Paths and symbols can identify an ownership boundary, architectural seam, required order, or canonical invariant. An exhaustive inventory of files and functions does not explain system boundaries or responsibilities.

## A human Overview can coexist with a rigorous contract

Progressive disclosure starts with a concise Overview of the consumer or architecture mental model, guarantees, limitations, and related owners. Detailed normative requirements and design invariants remain precise and authoritative.

## Template updates surface migrations without overwriting project documents

A newer template can raise the required documentation schema. The updater reports which project-specific documents need semantic migration, while preserving them for review. The migration belongs to the same downstream template-update Issue/PR; it is not a blind rewrite command.

See the [specification standard](specification.md), [design standard](design.md), [documentation synchronization standard](documentation-sync.md), and [template update standard](template-update.md).
