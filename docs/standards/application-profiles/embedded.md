# Embedded application profile

Apply this profile to an affected component whose application types include `embedded`. It supplements the base specification and design standards with target, hardware, timing, and firmware questions.

## Specification questions

- Which boards, processors, peripherals, toolchains, and target configurations are supported?
- What RAM, Flash, stack, power, and timing budgets constrain the behavior?
- What startup, reset, watchdog, sleep, wake, and degraded-hardware behavior is observable?
- How do firmware persistence, migration, rollback, and over-the-air updates behave when applicable?

## Design and verification questions

- How are cross-target builds and toolchain versions controlled and reproduced?
- Which interrupt handlers or real-time paths have deadlines, and which operations are forbidden in interrupt context?
- How are MMIO, DMA, cache coherence, ownership, and hardware errors isolated behind testable boundaries?
- What happens on watchdog expiry, brownout, partial update, storage failure, or interrupted startup?
- Which properties are established by unit tests, simulation, static analysis, SIL/HIL, or physical-hardware evidence? State hardware and firmware versions for each result.
- Check memory/stack budgets and timing margins on the relevant targets; do not infer hardware verification from a successful host build.
