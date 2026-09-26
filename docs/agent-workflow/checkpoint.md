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

Git/GitHub current state overrides stale checkpoint state.
