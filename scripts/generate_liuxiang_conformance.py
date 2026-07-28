"""Generate the 100-case synthetic Liuxiang conformance corpus.

The corpus is fictional and tests only deterministic engineering properties.
"""
from __future__ import annotations

import json
from pathlib import Path

DIMENSIONS = ["lx_ming", "lx_ye", "lx_yuan", "lx_meng", "lx_yuan_relation", "lx_shi"]
AGGREGATE_HASH = "sha256:1620423af9d7411b6329e971e5196c599cdd8914f9a3c6e8277ac4b1015f0944"


def signal(
    case_id: str,
    sequence: int,
    dimension: str,
    direction: str,
    magnitude: int,
    *,
    source: str = "synthetic_conformance",
    independent: str | None = None,
    shared: str | None = None,
    source_reliability: int = 9000,
    mapping_reliability: int = 9000,
    missing_penalty: int = 0,
    dispute_penalty: int = 0,
    boundary_penalty: int = 0,
    hard_conflict: bool = False,
) -> dict:
    signal_id = f"{case_id}:signal:{sequence:02d}"
    return {
        "schema_version": "signal-v2/1.0.0",
        "signal_id": signal_id,
        "subject_id": f"synthetic:{case_id}",
        "dimension_id": dimension,
        "direction": direction,
        "magnitude_bp": magnitude,
        "source_system": source,
        "source_record_id": f"{case_id}:record:{sequence:02d}",
        "source_fact_path": f"$.synthetic_signals[{sequence}]",
        "source_claim_ids": ["SANJI_SYNTHETIC_CONFORMANCE"],
        "source_dataset_id": "synthetic-conformance-v1",
        "source_dataset_revision": "1.0.0",
        "mapping_rule_id": "LX.SYNTHETIC.CONFORMANCE.V1",
        "mapping_ruleset_version": "liuxiang-mappings/1.0.0",
        "profile_id": "synthetic-profile-v1",
        "source_reliability_bp": source_reliability,
        "mapping_reliability_bp": mapping_reliability,
        "independence_group": independent or f"{case_id}:independent:{sequence:02d}",
        "shared_source_group": shared or f"{case_id}:source:{sequence:02d}",
        "temporal_scope": {"kind": "synthetic", "sequence": sequence},
        "supports": [dimension] if direction == "positive" else [],
        "counterevidence": [dimension] if direction == "negative" else [],
        "missingness": {"penalty_bp": missing_penalty, "facts": []},
        "disputes": {
            "penalty_bp": dispute_penalty,
            "hard_conflicts": [f"{case_id}:hard"] if hard_conflict else [],
            "soft_conflicts": [],
        },
        "boundary_sensitivity": {"penalty_bp": boundary_penalty},
        "trace_ref": f"synthetic:{signal_id}",
        "engine_version": "0.1.0",
    }


def build_case(index: int) -> dict:
    case_id = f"LX-{index + 1:03d}"
    kind = index % 10
    target = DIMENSIONS[(index // 10) % len(DIMENSIONS)]
    other = DIMENSIONS[(DIMENSIONS.index(target) + 1) % len(DIMENSIONS)]
    completeness = {dimension: 8000 for dimension in DIMENSIONS}
    values: list[dict] = []
    expected = "provisional"
    if kind == 0:  # obvious leader
        values = [signal(case_id, i, target, "positive", 9000) for i in range(3)]
        completeness[target] = 9500
        expected = "decisive"
    elif kind == 1:  # exact tie
        values = [
            signal(case_id, 1, target, "positive", 8000),
            signal(case_id, 2, other, "positive", 8000),
        ]
        expected = "contested"
    elif kind == 2:  # counterevidence
        values = [
            signal(case_id, 1, target, "positive", 8500),
            signal(case_id, 2, target, "negative", 4500),
        ]
    elif kind == 3:  # same-source duplicate does not become independent
        first = signal(case_id, 1, target, "positive", 8500, independent="same", shared="same")
        duplicate = {**first, "signal_id": f"{case_id}:signal:02", "trace_ref": f"synthetic:{case_id}:signal:02"}
        values = [first, duplicate]
    elif kind == 4:  # profile dispute
        values = [
            signal(case_id, 1, target, "positive", 9000, dispute_penalty=7000),
            signal(case_id, 2, target, "positive", 8000, dispute_penalty=7000),
        ]
        completeness[target] = 6500
    elif kind == 5:  # boundary sensitivity
        values = [
            signal(case_id, 1, target, "positive", 9000, boundary_penalty=8000),
            signal(case_id, 2, target, "positive", 8000, boundary_penalty=8000),
        ]
        completeness[target] = 7000
    elif kind == 6:  # severe missingness
        values = []
        completeness = {dimension: 2000 for dimension in DIMENSIONS}
        expected = "insufficient"
    elif kind == 7:  # high strength, low confidence
        values = [
            signal(
                case_id, 1, target, "positive", 10000,
                source_reliability=5000, mapping_reliability=10000,
                dispute_penalty=8000, boundary_penalty=8000,
            ),
            signal(
                case_id, 2, target, "positive", 10000,
                source_reliability=5000, mapping_reliability=10000,
                dispute_penalty=8000, boundary_penalty=8000,
            ),
        ]
        completeness[target] = 4500
    elif kind == 8:  # independent multi-system consistency
        values = [
            signal(case_id, 1, target, "positive", 8500),
            signal(case_id, 2, target, "positive", 8500),
            signal(case_id, 3, target, "positive", 8500),
        ]
        for value, system in zip(values, ("yijing", "bazi", "ziwei")):
            value["supports"].append(f"synthetic_system:{system}")
        expected = "decisive"
    else:  # hard conflict
        values = [
            signal(case_id, 1, target, "positive", 9000, hard_conflict=True),
            signal(case_id, 2, target, "negative", 8000, hard_conflict=True),
        ]
        expected = "contested"
    return {
        "case_id": case_id,
        "case_class": [
            "obvious_leader", "tie", "counterevidence", "same_source_duplicate",
            "profile_dispute", "boundary_sensitive", "severe_missingness",
            "high_strength_low_confidence", "multi_system_consistency",
            "hard_conflict",
        ][kind],
        "synthetic_notice": "完全虚构，仅用于确定性契约验证，不构成现实验证。",
        "expected_status": expected,
        "snapshot": {
            "operation": "run_liuxiang_research_v1",
            "subject_id": f"synthetic:{case_id}",
            "signals": values,
            "completeness_bp_by_dimension": completeness,
        },
    }


def main() -> None:
    output = Path("packages/sanji-engine/src/sanji_engine/golden_cases/liuxiang/synthetic-conformance-v1.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "liuxiang-synthetic-conformance/1.0.0",
        "asset_class": "synthetic_conformance",
        "reality_validation": False,
        "case_count": 100,
        "aggregate_hash": AGGREGATE_HASH,
        "cases": [build_case(index) for index in range(100)],
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
