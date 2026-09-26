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
