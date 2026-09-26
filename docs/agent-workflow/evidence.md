# Evidence

Temporary Issue-scoped evidence:

```text
.agent-state/issues/<issue>/
  screenshots/
  logs/
```

Durable small evidence, when necessary:

```text
docs/issues/<issue>-<slug>/evidence/
```

Rules:

- keep raw logs/temp screenshots local;
- commit only evidence useful for future review/reference;
- use CI artifacts for large logs/videos/dumps;
- never store secrets, tokens, private data, or unnecessary machine-specific paths.
