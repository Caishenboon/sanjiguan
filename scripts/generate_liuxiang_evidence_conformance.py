"""Generate the 72-case private-evidence synthetic conformance asset."""
from __future__ import annotations

import json
from pathlib import Path

from sanji_engine.canonical import content_hash
from sanji_engine.signals.evidence_v1 import run_liuxiang_evidence_v1

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "sanji-engine" / "src" / "sanji_engine" / "golden_cases" / "liuxiang" / "user-evidence-conformance-v1.json"
DIMENSIONS = ("lx_ming", "lx_ye", "lx_yuan", "lx_meng", "lx_yuan_relation", "lx_shi")


def fact(dimension: str, index: int, day: int, **changes) -> dict:
    value = {
        "record_id": f"{dimension}:record:{index}",
        "dimension_id": dimension,
        "fact_kind": "evidence",
        "occurred_on": f"2026-01-{day:02d}",
        "date_precision": "exact_date",
        "state": {
            "lx_yuan": "sustained",
            "lx_meng": "confirmed_tag",
            "lx_yuan_relation": "interaction",
            "lx_shi": "documented",
        }.get(dimension, "repeated"),
        "direction": "positive",
        "source_reliability_bp": 8000,
        "confirmed_tags": ["user-confirmed"] if dimension == "lx_meng" else [],
        "coverage_fields": {},
        "profile_id": "synthetic-subject",
        "withdrawn": False,
        "counterevidence": [],
        "conflicts": [],
        "relationship_confirmation": "mutual" if dimension == "lx_yuan_relation" else "not_applicable",
        "consent_active": True,
        "profile_dispute_bp": 0,
        "boundary_sensitivity_bp": 0,
        "source_type": "synthetic_conformance",
        "verification_status": "synthetic_only",
    }
    value.update(changes)
    return value


def snapshots(dimension: str) -> list[tuple[str, list[dict], list[str]]]:
    base = [fact(dimension, 1, 1), fact(dimension, 2, 16), fact(dimension, 3, 31)]
    coverage = fact(dimension, 0, 1, fact_kind="coverage", direction="neutral")
    if dimension == "lx_ming":
        coverage["coverage_fields"] = {
            "birth_date": True, "birth_time_precision": True,
            "birth_place": True, "timezone": True,
        }
    return [
        ("coverage_only", [coverage], []),
        ("single_record", [base[0]], []),
        ("cross_date_independent", base, []),
        ("duplicate_record_tags", base + [dict(base[0], confirmed_tags=["a", "b"])], []),
        ("same_day_cap", [base[0], fact(dimension, 2, 1), fact(dimension, 3, 1)], []),
        ("counterevidence", base + [fact(dimension, 4, 30, direction="negative")], []),
        ("withdrawn", base + [fact(dimension, 4, 30, withdrawn=True)], []),
        ("excluded", base + [fact(dimension, 4, 30)], [f"{dimension}:record:4"]),
        ("boundary_sensitive", base + [fact(dimension, 4, 30, boundary_sensitivity_bp=5000)], []),
        ("profile_dispute", base + [fact(dimension, 4, 30, profile_dispute_bp=5000)], []),
        ("hard_soft_conflict", base + [fact(dimension, 4, 30, conflicts=["explicit_conflict"])], []),
        (
            "precision_preserved",
            base + [fact(dimension, 4, 30, occurred_on="2024", date_precision="year_only")],
            [],
        ),
    ]


def main() -> None:
    cases = []
    hashes = []
    for dimension in DIMENSIONS:
        for index, (scenario, facts, excluded) in enumerate(snapshots(dimension), 1):
            case_id = f"{dimension}-{index:02d}-{scenario}"
            snapshot = {
                "operation": "run_liuxiang_evidence_v1",
                "subject_id": "synthetic-subject",
                "facts": facts,
                "excluded_record_ids": excluded,
            }
            result, trace = run_liuxiang_evidence_v1(snapshot)
            case = {
                "case_id": case_id,
                "asset_class": "synthetic_conformance",
                "dimension_id": dimension,
                "scenario": scenario,
                "snapshot": snapshot,
                "expected_status": result["status"],
                "result_hash": result["result_hash"],
                "trace_hash": content_hash(trace),
            }
            cases.append(case)
            hashes.append({
                "case_id": case_id,
                "result_hash": result["result_hash"],
                "trace_hash": case["trace_hash"],
            })
    asset = {
        "schema_version": "liuxiang-user-evidence-conformance/1.0.0",
        "asset_class": "synthetic_conformance",
        "case_count": len(cases),
        "notice": "完全虚构；仅证明确定性、策略与回放一致性，不证明现实有效性。",
        "cases": cases,
        "aggregate_hash": content_hash(hashes),
    }
    OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(asset["case_count"], asset["aggregate_hash"])


if __name__ == "__main__":
    main()
