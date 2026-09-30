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

For a PR handoff, publish the validated Self-review as one top-level PR conversation comment. The PR body records only its comment ID, SHA-256, and Reviewed-HEAD. Another reviewer can run `validate-public-review.*` to fetch that one comment and compare it with the current effective Reviewer Checklist and PR HEAD. A PASS result does not establish that cited evidence is truthful; reviewers must inspect the referenced diff, test output, and CI run independently.
