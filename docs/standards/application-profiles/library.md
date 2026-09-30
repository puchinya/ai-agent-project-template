# Library application profile

Apply this profile to an affected component whose application types include `library`. It supplements the base specification and design standards with downstream-consumer questions.

## Specification questions

- Which public APIs, symbols, data formats, and ABI surfaces are supported?
- What compatibility guarantees apply across releases, including semantic versioning and deprecation?
- Which feature flags, configuration combinations, and supported platform/runtime matrix are public?
- What ownership, lifetime, error, thread-safety, and reentrancy guarantees do consumers observe?

## Design and verification questions

- Which modules own public contracts, and how are internal changes prevented from leaking into the API accidentally?
- How are feature combinations and platform differences kept coherent without creating unsupported combinations?
- What are the resource ownership and thread-safety rules for callers, and how are misuse cases surfaced?
- Which downstream compatibility tests, compile fixtures, ABI checks, or consumer examples demonstrate the contract?
- How are deprecations, migration guidance, and breaking changes reviewed before release?
