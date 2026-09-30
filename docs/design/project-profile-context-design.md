<!-- agent-doc-type: design -->
<!-- agent-doc-schema: 2 -->
# Project Profile and Context Design

- Status: Approved
- Owning Issue: [Issue #3](https://github.com/puchinya/ai-agent-project-template/issues/3)
- Related specification: [Project Profile and Agent Context Specification](../specs/project-profile-spec.md)

## Overview

The project profile remains one small JSON source of truth. The CLI validates it once at load time, then routes context or verification through the selected components. Application type selects additional standards; stack, application type, target, and runtime host stay independent. Context generation reads the Issue's affected-component section and emits paths and metadata only. Verification composes project, component, and compatible-target hooks in a deterministic sequence. Schema-1 profiles keep their existing path through the tool.

## Context and goals

Issue #3 extends `scripts/agent/agent_tool.py` from a flat stack profile to a component-aware profile without duplicating the shared workflow or the existing documentation-tooling contract. The architecture goals are to keep configuration normalization at one boundary, make routing deterministic and compact, keep machine authority in `.agent/project.json`, and avoid persistent runtime state. Observable guarantees are owned by the [specification](../specs/project-profile-spec.md).

## Requirements traceability

| Requirement/spec section | Design consequence |
|---|---|
| [Profile schema](../specs/project-profile-spec.md#profile-schema) | `load_config` owns schema dispatch, schema-2 validation, and a normalized view while preserving schema-1 input and semantics. |
| [Initialization](../specs/project-profile-spec.md#initialization) | `cmd_init` builds a schema-2 root component from explicit inputs and existing stack detectors; unknown stacks receive no defaults. |
| [Issue component routing](../specs/project-profile-spec.md#issue-component-routing) | `cmd_context` parses the canonical Issue section and resolves IDs against the validated profile before formatting output. |
| [Hook selection and ordering](../specs/project-profile-spec.md#hook-selection-and-ordering) | `cmd_run_hook` composes hooks from validated scopes in configuration order and gates target commands with runtime-host compatibility. |
| [Context routing output](../specs/project-profile-spec.md#context-routing-output) | The context formatter emits a fixed set of existing and routing keys, not source/document bodies. |
| [Application profiles and template ownership](../specs/project-profile-spec.md#application-profiles-and-template-ownership) | The manifest builder recursively finds nested standards and explicitly adds the shared profile specification while excluding design/project-specific owners. |

## Architecture overview

```text
.agent/project.json
       |
       v
load_config: decode -> schema dispatch -> validate -> normalized profile
       |                                  |
       |                                  +--> init-project writes schema 2
       |
       +--> agent-context: Issue section -> affected component IDs -> routing manifest
       |
       +--> run-hook: global hooks -> selected component hooks -> compatible target hooks
                                      ^
                                      |
                             runtime host detection
```

`agent_tool.py` remains the single CLI and orchestration boundary. It has no separate service, database, or cache. Markdown standards remain independently owned documents and are referred to by path. Template manifest generation manages only shared template files.

## Architecture invariants

- `.agent/project.json` is the only machine authority for project profile configuration.
- Validation happens before profile-dependent output or hook command execution.
- Schema 1 uses the legacy profile/hook path and is never normalized back to disk.
- Schema 2 stores component, stack, application type, and target separately. Runtime host is detected for each invocation and never stored.
- Issue routing selects configured component IDs; application types select standards paths; neither stack nor host selects an application type.
- Hook composition is sequential. Scope and configuration order are observable and stable.
- Context generation is read-only and emits routing metadata only.
- Profile validation and routing create no persistent state. Existing Issue-local state stays under `.agent-state/issues/<issue>/`.
- The shared specification is template-managed by explicit path. The design and arbitrary project-specific durable docs are not manifest-managed.

## Component responsibilities

| Component/module | Responsibility | Must not own |
|---|---|---|
| `load_config` and profile helpers | Decode schema 1/2, validate schema-2 shape, and expose values to consumers. | Writing migrations or inferring application behavior. |
| `detect_stacks` / `default_hooks` | Detect existing built-in technologies and provide only known default commands. | Application-type detection or commands for opaque stacks. |
| `cmd_init` | Construct and write deterministic schema-2 defaults and generated human-readable summary. | Runtime-host persistence or unrequested framework detection. |
| `cmd_run_hook` | Select scopes, detect runtime host, compose, and execute hook commands in order. | Parallel execution, hidden target execution, or component/target branch-switch hooks. |
| `cmd_context` | Read Issue/profile/runtime metadata, resolve affected components, and print the routing manifest. | Inlining source/specification/design contents or editing repository files. |
| `cmd_refresh_template_manifest` | Enumerate shared template files, including nested standards, and explicitly include shared tooling specifications. | Managing arbitrary project-specific specifications, designs, or status. |
| Application-profile Markdown | Own only additional conditional review prompts for one behavior type. | Replacing or duplicating base specification/design standards. |

Dependency direction is `profile validation -> routing/selection -> formatting or command execution`. Standards are leaves referenced by routing metadata; they do not control profile parsing.

## Data and control flow

### Profile load and initialization

`load_config` reads the profile and dispatches on `schema_version`. Schema 1 is passed through the legacy consumer behavior. Schema 2 is checked for required object/array/string shapes, unique component IDs, safe repository-relative roots, non-empty stack IDs, valid application types, per-component target ID uniqueness, valid `runnable_on` values, and arrays of non-empty hook commands. Failure occurs before a caller executes configured commands.

`cmd_init` obtains stacks from the existing detectors unless an explicit `--stack` list is supplied. Built-in stacks may receive their existing defaults. Opaque stack IDs are stored without guessed commands. It creates one root component by default, uses `generic` unless an application type is explicit, and gives CLI-created target IDs the neutral `runnable_on: ["any"]` default. `cargo clean` is inserted only when explicitly enabled.

### Context routing

1. `cmd_context` retrieves Issue phase/labels and the Issue body through the existing GitHub CLI boundary, then loads and validates `.agent/project.json`.
2. For schema 1, it selects the legacy root project scope. For schema 2, it parses the canonical `## Affected components` list. One configured component is selected implicitly when the section is absent; multiple components require the section. Unknown IDs fail before a manifest is printed.
3. It detects normalized runtime OS and architecture for the invocation. Host data is not written to configuration.
4. It prints existing Issue/worktree/PR/contract fields and adds schema, host, selected component metadata, and applicable deduplicated profile paths. It never reads profile Markdown bodies to format the manifest.

Component metadata follows component configuration order. Applicable non-generic profile paths are de-duplicated and sorted by application-type identifier, which keeps output stable even when multiple components share a profile.

### Verification hook composition

For schema 1, `cmd_run_hook` continues to resolve the existing flat hook list. For schema 2 it validates the requested component IDs, detects the current host, then creates an in-memory ordered command sequence:

1. project-level commands for the requested verification hook;
2. selected component commands in component configuration order;
3. each selected component's target commands in target configuration order when `runnable_on` contains the host OS or `any`.

Each scope preserves command-list order. A repeated `--component` selection limits component and target hooks while project-level verification still runs. With no selection, all components are selected. An incompatible target emits the specified skip diagnostic and contributes no command to execution; compatible components/targets continue. Commands and skip diagnostics are executed sequentially from the ordered step list using the existing shell runner so failure behavior remains visible to the invoking process. When the first command token is `python` or `python3` and that executable is absent, the runner substitutes the other alias while preserving the remainder; it does not rewrite other command text.

### Persistence and cache

N/A for runtime caches and databases — this CLI performs one-shot reads and execution. The project profile is the persistent source of truth. Contract, evidence, and review artifacts remain Issue-local under `.agent-state/issues/<issue>/` and are separate from project profile normalization.

## Ownership and lifecycle

Profile data is loaded for one CLI invocation and released when the process exits. `cmd_context` owns its GitHub CLI result only for the duration of formatting. `cmd_run_hook` owns each sequential child command until completion and returns its failure through the existing command path. The change introduces no daemon, callback, subscription, shared mutable cache, or background task; there is no destruction order beyond normal process and child-process completion. Signals and operating-system process termination remain the existing shell runner's responsibility.

## Error handling and recovery

| Failure point | Result / propagation | Cleanup | Retry / recovery |
|---|---|---|---|
| Missing, malformed, or unsupported profile | Deterministic CLI error before routing or hook execution. | No profile file is rewritten. | Correct the profile and rerun. |
| Invalid component/target/root/hook definition | Identify the invalid profile area and fail validation before any configured hook command runs. | No command sequence is started. | Correct the offending definition and rerun. |
| Missing multi-component Issue routing or unknown component | `agent-context` fails with the required section or unknown ID identified; it prints no partial manifest. | No repository files are changed. | Add valid component IDs to the Issue and rerun. |
| GitHub/Git dependency failure while generating context | Propagate a clear command failure; no partial output is treated as a complete manifest. | No repository files are changed. | Restore dependency access and rerun. |
| Host-incompatible target | Emit `SKIPPED_TARGET_VERIFICATION ... reason=host_mismatch`; continue other selected verification and record the target unverified. | The skipped target command never starts. | Run that target on a compatible host. |
| Hook command failure | Preserve existing shell-runner failure propagation; later behavior follows the existing runner contract. | Completed child process resources are released by the shell/process runtime. | Fix the command or dependency and rerun verification. |

Repeated context and initialization calls are deterministic for unchanged inputs. The runner does not parallelize hooks, so no reentrancy or shared-state ordering is introduced.

## Concurrency and async model

N/A for internal concurrency and asynchronous work — `agent_tool.py` is a synchronous one-shot CLI. Hook commands run sequentially. Runtime host checks and context formatting occur in the same invocation; no concurrent cache or background task exists. Cancellation remains process/shell signal behavior and is not converted into a separate profile-level API.

## Quality attributes and operations

### Security

Root validation prevents profile paths from escaping the repository. Hook commands remain trusted project configuration and are not sandboxed by component or target selection. Issue text is parsed only for the canonical component section; it is not executed. Context output avoids copying source/document bodies.

### Performance and resource strategy

Profile validation, selection, and manifest formatting are linear in configured components, targets, and application types. The design adds no index, cache, or database. Hook commands execute sequentially, matching their declared order and avoiding concurrent resource contention.

### Observability, diagnostics, and supportability

Validation errors identify the invalid schema area. Multi-component routing diagnostics name the required section. Host skips use the stable `SKIPPED_TARGET_VERIFICATION` line so operators can copy them into the Completion Report as unverified targets. Actual verification results remain task evidence, not durable design state.

### Platform / backend / deployment considerations

Runtime host detection maps the host OS to `windows`, `macos`, or `linux`, and reports OS/architecture in context output. `runnable_on` matching uses the normalized OS; target IDs do not imply compatibility. GUI, mobile, server, embedded, and library backend concerns live in their selected application-profile standards. This tooling has no deployment or rollout service.

## Compatibility and migration

Schema-1 profiles remain on the existing consumer path with no file rewrite. Schema-2 profiles are validated and consumed by the new component-aware path. `init-project` is the explicit point that writes schema 2; it does not migrate an existing profile unless invoked under the existing initialization rules. Template updates continue to preserve project-specific profile and generated project summary files. Documentation schema remains 2; the template release version is `0.5.0`.

## Verification strategy

| Risk/invariant | Verification method |
|---|---|
| Schema-1 semantics accidentally change | Load and run a schema-1 fixture; assert the exact existing flat command list. |
| Invalid profile partially executes commands | Mock shell execution and assert zero calls for every invalid schema-2 fixture. |
| Initialization infers types or re-enables cargo clean | Initialize Rust and explicit opaque-stack fixtures; inspect generated profile and hooks for default and explicit cargo-clean cases. |
| Issue routing selects too many components or accepts unknown IDs | Test single-component fallback, missing multi-component section, explicit IDs, and unknown IDs. |
| Context output becomes a document bundle | Assert required routing keys/paths and assert profile/spec/design text is absent. |
| Hook ordering or target skipping is wrong | Substitute command execution; assert exact global/component/target order and that mismatched target commands were never invoked. |
| Application profiles leak into unrelated components or manifest | Test deduplication, profile paths, nested standards inclusion, explicit shared-spec inclusion, and exclusion of arbitrary project-specific specs/designs. |
| Documentation ownership links break | Run `validate-docs` after adding both owners and indexes. |

Actual test and platform results are reported against the committed HEAD in the Issue/PR completion evidence.

## Alternatives considered

### Separate workflow for each application type

- Advantages: application-specific steps would be visible in separate documents.
- Rejected because: it duplicates shared phase workflow and causes requirements/design/review behavior to diverge. Conditional profiles add only application-specific checks.

### Infer application behavior from stack or repository files

- Advantages: fewer explicit profile inputs.
- Rejected because: a technology does not determine whether a component is GUI, server, library, or another behavior type; inference would be surprising and brittle.

### Persist the current host or prebuild commands for every stack

- Advantages: fewer runtime checks or more out-of-box commands.
- Rejected because: host data becomes stale across developers/CI, and unknown stacks cannot safely receive guessed commands. Runtime host stays ephemeral and stack identifiers stay extensible.

### Put every nested spec/design/status file in the template manifest

- Advantages: a broad recursive glob is simple.
- Rejected because: it would overwrite or conflict with downstream project-owned durable documents. Only nested shared standards and the explicit shared project-profile spec are managed.

## Risks and open follow-ups

- Multi-component routing depends on Issues using the canonical section and configured component IDs; requirements workflow guidance and actionable missing-section errors reduce omission risk.
- A target configured with `any` is intentionally runnable on every host. Maintainers who add platform-specific commands must narrow `runnable_on` before relying on host gating.
- Windows PowerShell wrapper behavior requires execution on Windows before it can be reported as verified.
- Targets created by `init-project --target` default to `runnable_on: ["any"]` because the CLI accepts only target IDs and has no host-selection input. Maintainers adding platform-specific commands must narrow compatibility before relying on target host gating.
