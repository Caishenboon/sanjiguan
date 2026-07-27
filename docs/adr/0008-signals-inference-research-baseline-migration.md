# ADR 0008: migrate the Signals / Inference research baseline

- Status: accepted for migration
- Scope: engineering equivalence only

## Decision

Move the existing deterministic research behavior into
`packages/sanji-engine`; preserve Engine API 1.0's four public functions.
Keep `packages/research_inference/engine.py` only as a shape-compatible adapter.
Freeze the behavior as `research_baseline` and prohibit production activation.

Existing binary-float behavior is compatibility-wrapped and serialized as
decimal strings at the canonical boundary. It is not recalibrated in this
Sprint. Engine-owned Trace and Replay Manifest become the authoritative
calculation audit artifacts, while application permissions and persistence
remain outside the engine.

## Consequences

Applications cannot independently score, rank, resolve conflicts, or decide a
verdict. The same request and version set is cross-platform hash-testable.
Research theory, weights and thresholds remain unvalidated. Future numeric
redesign requires a new ruleset/method version and cannot silently change this
historical baseline.

