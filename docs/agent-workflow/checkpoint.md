# Local work checkpoint

Use only when pausing/resuming incomplete Issue work.

```bash
scripts/agent/save-work-checkpoint.sh <issue>
scripts/agent/resume-work.sh <issue>
scripts/agent/agent-context.sh <issue>
```

PowerShell equivalents are available.

Checkpoint path:

```text
.agent-state/issues/<issue>/checkpoint.md
```

Keep it short: objective, completed work, current state, next action, checks, uncommitted work, blockers.

Never store reasoning transcripts, secrets, full logs, or duplicate Implementation Contract bodies.

Record only the contract mirror path/SHA and whether `verify-implementation-contract.* <issue>` passed; do not copy the contract body into the checkpoint. If the mirror is missing, use `restore-implementation-contract.*`. If it differs from the approved Issue pointer, stop and inspect both versions; replacing the local mirror requires `--replace-stale`, which preserves a SHA-named backup.

Git/GitHub current state overrides stale checkpoint state.
