# Signals / Inference research-baseline equivalence delivery

## Delivered

- Frozen 30 synthetic pre-migration cases and machine comparison.
- Signal validation/model, frozen assets and research-only ruleset.
- Candidate, evidence, counterevidence, conflict, score, rank, status and
  research-node behavior migrated into `sanji-engine`.
- Engine-owned canonical result, Trace and Replay Manifest.
- Thin legacy presentation adapter; existing owner-only access, consent,
  persistence, template fallback and prose-provider boundary remain.
- Native manifests are stored only for new engine runs using the additive
  Sprint foundation columns; historical NULL records are not fabricated.
- Ubuntu/Windows deterministic hash checks and static duplicate-logic gates.

The characterization fixture excludes only notice text, persistence/database
IDs, runtime timestamps, local paths and provider prose. It was not updated
after migration. Expected result: `30 / 30 equivalent`.

## Classification

Completed: engineering migration and replay infrastructure.

Frozen: prior research behavior for drift detection.

Not validated: theory, weights, thresholds, identities or production fitness.

Not implemented: formal Six Signals mappings/weights and all real Yijing,
Bazi, Ziwei, past-life, bardo, relationship and life-chart algorithms.

## Verification

Run:

```text
python scripts/capture_signals_inference_baseline.py
python -m unittest tests.test_sanji_engine_core tests.test_sanji_engine_research -v
python scripts/validate_sanji_engine.py
```

Any equivalence failure emits a structured field-path diff and blocks
migration. The PR remains open for product-owner review.

