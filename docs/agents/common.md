# Common agent execution rules

- Prefer the smallest relevant investigation scope.
- Respect existing repository style and dependency boundaries.
- Avoid unrelated refactoring.
- Treat generated files and lockfiles as intentional changes requiring review.
- Use configured hooks rather than inventing replacement verification commands.
- Record untested environments honestly.
- Keep secrets out of prompts, logs, Issue bodies, PRs, docs, and `.agent-state/`.
