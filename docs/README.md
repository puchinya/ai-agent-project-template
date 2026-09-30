# Documentation router

| Need | Start here |
|---|---|
| externally observable behavior / API / protocol | `specs/` |
| durable architecture / ownership / data flow | `design/` |
| current implementation / known gap / verification state | `status/` |
| technology and repository execution rules | `agents/` |
| Issue phase workflow | `agent-workflow/` |
| document quality requirements | `standards/` |
| conditional checks for selected application types | [`standards/application-profiles/`](standards/application-profiles/README.md) |
| document starting points | `templates/` |

Dependency direction:

```text
specs -> design -> code -> status
```

Start with one category and the smallest relevant set of documents. Do not load all documentation by default.
