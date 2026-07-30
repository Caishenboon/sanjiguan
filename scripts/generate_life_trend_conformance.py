"""Regenerate the reviewed synthetic-only Sprint 18 conformance asset."""
from __future__ import annotations

import json
from pathlib import Path

from sanji_engine import execute
from sanji_engine.canonical import content_hash
from tests.test_sanji_engine_life_trend_v1 import domain, request, synthetic_cases

TARGET = Path(
    "packages/sanji-engine/src/sanji_engine/golden_cases/life_trend/"
    "life-trend-conformance-v1.json"
)

results = []
for index, case in enumerate(synthetic_cases(), 1):
    value = domain(execute(request(case["factors"], run_suffix=index)))
    results.append({
        "case_id": case["case_id"],
        "core_output_hash": value["core_output_hash"],
        "trace_hash": value["trace_hash"],
        "result_hash": value["result_hash"],
    })
asset = {
    "schema_version": "life-trend-conformance/1.0.0",
    "classification": "synthetic_conformance",
    "case_count": len(results),
    "cross_platform_requirement": "Windows and Linux hashes must match exactly",
    "cases": results,
    "aggregate_hash": content_hash(results),
}
TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text(json.dumps(asset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(asset["case_count"], asset["aggregate_hash"])
