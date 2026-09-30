# Server application profile

Apply this profile to an affected component whose application types include `server`. It supplements the base specification and design standards with service lifecycle and operational questions.

## Specification questions

- What are the request, job, or stream lifecycle guarantees, including partial completion and externally visible failure?
- Which timeout, cancellation, retry, idempotency, and ordering behaviors are part of the contract?
- What consistency, durability, retention, and migration guarantees apply to persisted state?
- Which externally meaningful latency, throughput, availability, or resource objectives constrain behavior?

## Design and verification questions

- How are concurrency limits, queues, backpressure, fairness, and overload rejection enforced?
- How do deadlines and cancellation propagate through dependencies? Which operations are safe to retry?
- How does graceful shutdown drain or cancel work, release resources, and preserve durable state?
- What logs, metrics, traces, health checks, and alerts make failures and service impact diagnosable without leaking sensitive data?
- How are deployment, rollout, compatibility, rollback, and data migration coordinated? Which failure modes require an operational recovery path?
- Verify idempotency, overload, timeout, shutdown, migration, and observability behavior where relevant; state any untested deployment or scale boundary.
