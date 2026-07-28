# Deterministic Liuxiang Research Platform v1

Liuxiang v1 is a Sanjiguan-original, research-only deterministic system. It is
`research_active`, `UNCONFIRMED`, and never production-activatable.

Signal v2 records the exact source record, fact path, dataset revision, mapping
rule, profile, independence group, shared-source group, reliability, missingness,
disputes, boundary sensitivity, trace reference, and canonical content hash.
Strength and confidence are separate integer basis-point values.

The pipeline deduplicates identical fact/mapping paths and caps each shared
provider to its strongest contribution per dimension and direction. Oracle and
LLM output cannot create evidence, affect scores, change rank, or enter replay
hashes. Yijing, Bazi, and Ziwei adapters expose mechanical facts only; their
Liuxiang semantic mappings remain disabled until reviewed.

Public datasets are pinned by revision and SHA-256. Raw data is not committed.
DreamBank text is not downloaded because the original-to-repackaged license
chain has not been established. External observations may propose a draft rule
for human review, but can never promote a runtime ruleset automatically.

Synthetic conformance proves reproducibility, source deduplication, state
transitions, trace, replay, input-order invariance, and cross-platform hashes.
It does not establish real-world validity, predictive power, or causality.
