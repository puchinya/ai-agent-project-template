# Conditional application profiles

Apply a profile only when the affected schema-2 component lists its application type in `.agent/project.json`. A profile supplements the [specification standard](../specification.md) or [design standard](../design.md); it does not replace or duplicate either base standard. `generic` selects no additional profile. Read only profiles selected by the affected components.

| Application type | Conditional standard |
|---|---|
| `desktop-gui` | [Desktop GUI](desktop-gui.md) |
| `cli` | [Command-line interface](cli.md) |
| `mobile` | [Mobile](mobile.md) |
| `server` | [Server](server.md) |
| `embedded` | [Embedded](embedded.md) |
| `library` | [Library](library.md) |

For each applicable profile, consider only questions relevant to the feature. Record observable guarantees in the specification, durable decisions in the design, and verification evidence in tests or status/evidence records.
