# Documentation synchronization standard

Use this responsibility chain:

```text
requirements -> specs -> design -> code/tests -> status
```

## Change impact

| Change | Specs | Design | Status |
|---|---|---|---|
| externally observable behavior/API/protocol | update first | if architecture changes | update current state |
| durable architecture/ownership/threading | only if contract changes | update first | update current state |
| implementation-only refactor | no | only if durable design changes | usually no |
| bug fix conforming to existing contract | no | only if prior design was wrong/incomplete | update if tracked gap closes |
| verification-only change | no | test strategy only if durable | update verification state if useful |

A document update is required because its responsibility changed, not merely because code changed.

Never rewrite historical evidence into `docs/status/`. Keep status concise and current.
