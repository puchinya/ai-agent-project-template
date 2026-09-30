<!-- agent-doc-type: specification -->
<!-- agent-doc-schema: 2 -->
# Project Profile and Agent Context Specification

- Status: Approved
- Owning Issue: [Issue #3](https://github.com/puchinya/ai-agent-project-template/issues/3)
- Related design: [Project Profile and Context Design](https://github.com/puchinya/ai-agent-project-template/blob/main/docs/design/project-profile-context-design.md)

## Overview

Project profiles describe the independently developed parts of a repository, the technologies each part uses, the software behavior it provides, and the targets it can build or verify. The common Issue workflow stays the same for every application type. `agent-context` uses profile data and an Issue's affected-component list to name the small set of documents and components an agent should inspect. `run-hook` combines project, component, and host-compatible target verification in a stable order. Schema-1 profiles remain readable with their current behavior. The [Agent Tooling Specification](agent-tooling-spec.md) remains the owner of the separate `validate-docs` and `update-template` CLI contract.

## Purpose

This specification defines the observable configuration and CLI behavior for `.agent/project.json` schema 1 and schema 2, `init-project`, `agent-context`, and `run-hook`. It serves project maintainers, agents routing work, and tooling that initializes or verifies repositories.

## Scope

### In scope

- Schema-2 profile shape and validation.
- Separation of components, stacks, application types, targets, and runtime host.
- Schema-2 initialization defaults and CLI inputs.
- Issue affected-component routing and compact context output.
- Project, component, and target verification selection and ordering.
- Compatibility with schema-1 project profiles and safe template ownership boundaries.

### Out of scope

- The `validate-docs` and `update-template` stable CLI contract, owned by the [Agent Tooling Specification](agent-tooling-spec.md).
- Application-specific workflow copies, framework detection beyond existing built-in stack detectors, and commands for unknown stacks.
- Project-specific specification, design, or status documents as template-managed files.

## Terminology

| Term | Meaning |
|---|---|
| Component | An independently developed or verified unit within a repository. |
| Stack | An implementation technology identifier, independent of application behavior. |
| Application type | A software behavior profile that selects additional review standards. |
| Target | A named build, run, or verification destination with host compatibility metadata. |
| Runtime host | The operating system and architecture executing an agent tool command. It is detected at runtime and is not project configuration. |
| Affected component | A configured component named by an Issue for context and verification routing. |
| Legacy root scope | The whole repository scope used by a schema-1 profile, which has no component list. |

## Semantic ownership

This document owns project-profile schemas, component/stack/application-type/target meaning, initialization defaults, affected-component parsing, context-routing output, and verification selection/skip behavior. The [Project Profile and Context Design](https://github.com/puchinya/ai-agent-project-template/blob/main/docs/design/project-profile-context-design.md) owns internal validation, routing, host-detection, and hook-composition architecture. The [Agent Tooling Specification](agent-tooling-spec.md) continues to own `validate-docs` and `update-template` behavior.

## Normative requirements

### Profile schema

- A project profile MUST declare `schema_version: 1` or `schema_version: 2`. An unsupported version MUST fail with a clear error.
- Schema 1 MUST remain readable, MUST NOT be rewritten automatically, and MUST retain its current flat project-wide hook behavior.
- New `init-project` output MUST use schema 2.
- A schema-2 profile MUST use the following distinct concepts:
  - `components`: repository development and verification units;
  - component `stacks`: non-empty technology identifiers;
  - component `application_types`: one or more behavior profiles;
  - component `targets`: build/run/verification destinations;
  - target `runnable_on`: operating systems on which target hooks may run.
- Schema 2 MUST retain the existing `branch`, `milestones`, and project-level `hooks` responsibilities. Project-level hooks own `branch_switch`, `verify_quick`, and `verify_final`; component and target hooks own only `verify_quick` and `verify_final`.
- A component MUST have a unique `id`, safe repository-relative `roots`, non-empty stack identifiers, recognized application types, a target list, and component verification hooks. A target MUST have a unique ID within its component, a `runnable_on` list, and target verification hooks.
- A schema-2 target MAY include a `requirements` object containing the three string-array fields `architectures`, `tools`, and `capabilities`. When present, all three arrays MUST be present; arrays MAY be empty and each value MUST be a non-empty string. Omitting the object MUST preserve the prior Schema 2 behavior.
- Component and target IDs used in context manifest fields MUST be free of commas, equals signs, line separators, and control characters. Root and stack values MUST also be free of these delimiters because they are emitted in comma-separated values in the line-oriented key/value context manifest.
- Roots MUST NOT be absolute or escape the repository. The repository root `.` is valid.
- Hook values MUST be arrays of non-empty command strings. `branch_switch` MUST NOT be configured on components or targets.
- `runnable_on` values MUST be drawn from `any`, `windows`, `macos`, and `linux`.
- The built-in application types MUST be exactly `generic`, `desktop-gui`, `cli`, `mobile`, `server`, `embedded`, and `library`. `generic` is a fallback and MUST NOT select an application-profile document.
- Application type MUST NOT be inferred from stack, target, repository contents, or runtime host.
- `generic` MUST remain a legal application type. Initialization MUST emit a warning when it initializes a component with `generic`; application type MUST NOT be guessed from other project data.
- Unknown explicit non-empty stack identifiers MUST be accepted as opaque values. Tooling MUST NOT invent detection, build, or verification commands for them.

### Initialization

- The default schema-2 component MUST be `id: root`, `roots: ["."]`, `application_types: ["generic"]`, and `targets: []`; its stacks MUST come from the existing detectors.
- `init-project` MUST validate the complete generated profile before writing it. `init-project --application-type <comma-separated values>` MUST set the requested built-in application types. When omitted, it MUST use `generic`.
- `init-project --target <comma-separated target ids>` MUST add the requested targets to the root component. A newly generated target MUST use `runnable_on: ["any"]` until a maintainer narrows its compatibility in the profile.
- Rust `cargo clean` MUST be off by default. Only an explicit `--cargo-clean on` MAY add `cargo clean` to the global `branch_switch` hook.
- Repeated initialization with the same inputs MUST produce deterministic profile and summary output.

### Issue component routing

- A multi-component schema-2 Issue MUST identify affected components using this canonical section:

  ```markdown
  ## Affected components

  - `desktop`
  - `server`
  ```

- A schema-2 project with one component MUST select that component when the Issue omits the section.
- A schema-2 project with multiple components MUST fail context routing when the section is missing or empty, and the diagnostic MUST identify `## Affected components` as the required section.
- Every listed component ID MUST exist in the project profile; an unknown ID MUST fail. The word `all` has no special meaning and is not an alias for selecting every component.
- Schema-1 profiles MUST retain whole-repository routing.
- `run-hook verify_quick --issue N` MUST select only the components listed in Issue N's canonical `## Affected components` section. This option MUST NOT be combined with `--component`. Missing or invalid Issue component data MUST fail before any verification command executes.

### Hook selection and ordering

- Schema-1 `run-hook` calls MUST preserve current behavior.
- Schema-2 `run-hook verify_quick` and `run-hook verify_final` MUST accept repeatable `--component <id>` options. Unknown component IDs MUST fail.
- Without a component selection, schema-2 verification MUST select all components. With a selection, it MUST run only the selected components' hooks, while still running the matching project-level hooks.
- `verify_quick` MUST accept `--issue N` as an alternative to repeatable `--component` selection; the two selection forms are mutually exclusive. `verify_final` without a selection MUST continue to select every component. Schema 1 retains its current selection behavior.
- Commands MUST execute sequentially in this order: project-level commands, selected component commands, then compatible target commands. Preserve component configuration order, target configuration order, and command-list order.
- A target is compatible when `runnable_on` contains `any` or the detected runtime host operating system. Host operating systems are normalized as `windows`, `macos`, or `linux`.
- After the operating-system check, a target with `requirements` MUST match the normalized runtime architecture, every listed PATH tool, and every listed explicit capability before its hooks may run. Runtime architecture aliases MUST normalize `AMD64` and `x86_64` to `x86_64`, and `aarch64` and `arm64` to `arm64`. Tools MUST be resolved through `shutil.which`; capabilities are supplied through repeatable `--capability ID` options.
- Target compatibility checks MUST run in this order: OS, architecture, PATH tools, then capabilities. The first mismatch MUST determine the skip reason. A capability declaration is not runtime evidence that a capability works.
- Incompatible target commands MUST NOT execute. The runner MUST emit `SKIPPED_TARGET_VERIFICATION component=<id> target=<id> reason=host_mismatch`, MUST NOT treat that target as verified, and MUST allow the remaining compatible verification to proceed.
- Requirement mismatches MUST also skip without executing the target command, using `reason=architecture_mismatch`, `reason=missing_tool`, or `reason=missing_capability` as applicable. A skipped target is unverified.
- Skipped platforms or targets MUST be recorded as unverified in the PR Completion Report.
- For a hook command beginning with `python` or `python3`, the runner MUST use the other alias only when the requested executable is unavailable. It MUST preserve the remainder of the command. Other command text MUST NOT be rewritten.

### Context routing output

- `agent-context <issue>` MUST retain the existing fields `issue`, `phase`, `workflow`, `branch`, `head`, `default_branch`, `worktree`, `pr`, `contract_status`, and `contract_sha256`.
- It MUST add `profile_schema=<1|2>` and `runtime_host=<os>/<arch>`.
- It MUST add `affected_components=<comma-separated ids>` and, for each selected schema-2 component, `component.<id>.roots`, `component.<id>.stacks`, `component.<id>.application_types`, and `component.<id>.targets` fields.
- For each distinct applicable non-generic application type, it MUST emit one `application_profile=<repository-relative path>` line pointing to `docs/standards/application-profiles/<type>.md`. Profile paths MUST be deduplicated and deterministic.
- When Issue `## Document impact` explicitly links an existing owner inside this repository under `docs/specs/`, `docs/design/`, or `docs/status/`, context output MUST emit its repository-relative path as `document_owner=<path>`. A planned future owner path MUST be emitted as `planned_owner=<repo-relative-path>`; it MUST NOT be presented as an existing owner.
- Owner paths MUST be resolved only from explicit Document impact entries. Same-repository GitHub file links MUST be verified against the current repository identity. Ambiguous, malformed, or foreign-repository URLs MUST produce a bounded `document_impact_diagnostic` and MUST NOT be emitted as owner paths.
- Document owner output MUST contain paths only, never file contents, full Issue bodies, comment text, or unrelated links.
- It MUST NOT inline Issue bodies, profile text, specification/design text, or source contents. Its output is a routing manifest, not a document bundle.
- `agent-context` MUST NOT modify repository-controlled files.
- `AGENTS.md` and Issue workflow instructions MUST route agents through the owning Issue, active workflow, affected components, applicable conditional profiles, linked specification/design/status owners, relevant symbols/tests/dependencies, and current diff. They MUST NOT require reading every standard or the generated `docs/agents/project.md` by default.
- `docs/agents/project.md` MUST remain a generated human-readable summary. For schema 2 it MUST include a component summary table. `.agent/project.json` remains machine authority.

### Application profiles and template ownership

- The repository MUST provide concise conditional standards at:
  - `docs/standards/application-profiles/desktop-gui.md`
  - `docs/standards/application-profiles/cli.md`
  - `docs/standards/application-profiles/mobile.md`
  - `docs/standards/application-profiles/server.md`
  - `docs/standards/application-profiles/embedded.md`
  - `docs/standards/application-profiles/library.md`
- These standards MUST add checks to the base specification/design standards, not replace or duplicate them.
- Nested application-profile standards MUST be template-managed. `docs/specs/project-profile-spec.md` MUST be explicitly template-managed. The project-profile design and arbitrary project-specific specification, design, and status documents MUST NOT be added to the template manifest.
- The template version MUST be `0.6.0`; `documentation_schema_version` MUST remain `2`, and the manifest schema version MUST remain unchanged.
- Template update MUST continue to preserve project-specific `.agent/project.json` and `docs/agents/project.md` files.

## Observable behavior

### State model

Project profiles are persistent repository configuration. Runtime host is per invocation and is never persisted. `agent-context` is read-only. `init-project` creates a schema-2 profile. Schema-1 profiles remain in schema 1 until a maintainer explicitly edits them.

### Data / API / format contract

The schema-2 shape is:

```json
{
  "schema_version": 2,
  "initialized": true,
  "project_name": "example",
  "components": [
    {
      "id": "desktop",
      "roots": ["apps/desktop"],
      "stacks": ["rust", "custom-toolchain"],
      "application_types": ["desktop-gui", "library"],
      "targets": [
        {
          "id": "windows-x64",
          "runnable_on": ["windows"],
          "requirements": {
            "architectures": ["x86_64"],
            "tools": ["cargo"],
            "capabilities": []
          },
          "hooks": {"verify_quick": [], "verify_final": []}
        }
      ],
      "hooks": {"verify_quick": [], "verify_final": []}
    }
  ],
  "branch": {"prefix": "feature", "max_slug_length": 48},
  "milestones": {"enabled": false, "version_source": "auto"},
  "hooks": {
    "branch_switch": [],
    "verify_quick": [],
    "verify_final": []
  }
}
```

`init-project --target windows-x64,ios-device` creates target entries with `runnable_on: ["any"]` and empty verification hook arrays; the profile owner may then restrict each target to compatible hosts and add hooks. `init-project` MUST NOT set a target's host compatibility by parsing its ID.

Context output uses one key/value per line. Schema-2 `component.<id>.*` fields and `application_profile` lines are emitted only for selected components. Profile paths are relative to the repository root. Existing context fields remain present in their existing format.

## Error and boundary behavior

| Condition | Required behavior |
|---|---|
| Unsupported profile schema | Fail clearly before using profile values. |
| Malformed schema-2 component or hook value | Fail deterministically and identify the invalid profile area. |
| Duplicate component ID or duplicate target ID within a component | Fail deterministically. |
| Absolute or escaping component root | Fail deterministically; do not resolve it outside the repository. |
| Empty stack identifier or unknown application type | Fail deterministically. |
| Malformed Target `requirements` | Fail profile validation before any configured verification command runs. |
| Runtime OS, architecture, PATH-tool, or capability mismatch | Emit `SKIPPED_TARGET_VERIFICATION component=<id> target=<id> reason=<host_mismatch|architecture_mismatch|missing_tool|missing_capability>`; do not execute the target and report it as unverified. |
| Ambiguous or foreign-repository Document impact URL | Emit a diagnostic and omit it from owner paths; do not fetch or inline linked content. |
| Invalid `runnable_on` value | Fail deterministically. |
| Multi-component Issue missing the affected-components section | Fail and name the required section. |
| Issue names a component that does not exist | Fail and identify the unknown ID. |
| Target does not match runtime host | Skip only that target, emit the stable diagnostic, and leave it unverified. |
| GitHub or local Git dependency fails during context generation | Propagate a clear command failure; do not write partial repository state. |

## Quality attributes

### Security and privacy

Profile roots are constrained to the repository. Context output contains routing metadata rather than source or full document bodies. Hook commands remain explicit repository configuration and run under the existing local execution trust model; profile scoping is not a security sandbox.

### Performance and scalability

Context generation emits metadata proportional to the selected components, targets, and application types. It MUST NOT load or print full conditional standards to achieve routing. Hook execution is sequential and follows the configured scope.

### Accessibility and usability

N/A — these project-profile commands and routing manifests are developer tooling without an end-user interface. GUI, mobile, and other user-facing product accessibility checks are routed through their conditional application standards.

### Portability and platform behavior

Runtime host names are normalized to `windows`, `macos`, and `linux`. Target compatibility is based on the runtime host, not the machine that authored or committed the profile. Windows PowerShell and Unix shell wrappers expose the same profile semantics.

## Compatibility and versioning

Schema 1 remains readable and preserves the existing flat hook behavior; there is no implicit migration. `init-project` writes schema 2 for new initialization. Unknown non-empty stacks are forward-compatible opaque identifiers, while application types and `runnable_on` values are constrained to the declared built-in sets. Schema-2 Targets without `requirements` retain the previous OS-only compatibility behavior. `update-template` does not overwrite a project's profile. The initial component-aware profile contract shipped with template version `0.5.0`; this extension ships with `0.6.0` while documentation schema 2 and manifest schema version remain stable.

## Acceptance traceability

| Requirement / acceptance criterion | Specification section | Verification |
|---|---|---|
| Schema-1 loading and flat hook compatibility; schema-2 validation | [Profile schema](#profile-schema) | `test_project_profile.py`: schema-1 compatibility and schema validation cases |
| Schema-2 initialization, opaque stacks, application types, and cargo-clean default | [Initialization](#initialization) | `test_project_profile.py`: initialization and stack/default cases |
| Affected-component routing and compact context manifest | [Issue component routing](#issue-component-routing), [Context routing output](#context-routing-output) | `test_project_profile.py`: single/multi routing and compactness cases |
| Existing and planned Document impact owner paths | [Context routing output](#context-routing-output) | `test_project_profile.py`: same-repository, planned, ambiguous URL, and path-only cases |
| Issue-scoped Quick selection and final all-component default | [Issue component routing](#issue-component-routing), [Hook selection and ordering](#hook-selection-and-ordering) | `test_project_profile.py`: exclusive selector and Issue component cases |
| Target OS/architecture/tool/capability gates and skip reasons | [Hook selection and ordering](#hook-selection-and-ordering) | `test_project_profile.py`: exact command order and zero-execution mismatch assertions |
| Conditional profiles and template ownership boundaries | [Application profiles and template ownership](#application-profiles-and-template-ownership) | `test_project_profile.py`: profile routing and manifest coverage; `validate-docs` |
| Failure, privacy, portability, and unverified-target reporting | [Error and boundary behavior](#error-and-boundary-behavior), [Quality attributes](#quality-attributes) | Focused tests plus configured final verification and Completion Report |
