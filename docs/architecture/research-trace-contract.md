# Research Trace contract

Engine Result, Ruleset Bundle, Replay Manifest, module results, and Trace use
versioned contracts and `sha256:` content hashes. Trace is machine-readable and
engine-owned.

The research chain has three ordered steps:

1. `signals:100:validate_and_deduplicate_signals`
2. `inference:200:generate_and_score_candidates`
3. `inference:300:rank_and_decide_status`

Each step records module, operation, input/output references, rule/source
references, deterministic parameters, sequence, and calculation hash. The
inference parameters contain per-candidate contributions, counterevidence and
conflicts; status trace records ranking and the status-decision reason.

The Replay Manifest freezes engine/API/canonicalization versions, ruleset ID
and hash, data and method versions, input hash, Trace hash, deterministic
context, and domain-result hashes. Missing or changed assets fail with stable
codes; a revoked bundle is rejected for a new run but remains usable for an
explicit historical replay. Legacy database rows with no native manifest stay
NULL and are never presented as replayable.

