"""Generate the 72 synthetic-only Sprint 17 conformance cases."""
from __future__ import annotations

import json
from pathlib import Path

from sanji_engine.canonical import content_hash
from sanji_engine.public import execute

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / (
    "packages/sanji-engine/src/sanji_engine/golden_cases/topics/"
    "topic-conformance-v1.json"
)


def request(topic: str, index: int) -> dict:
    facts = [
        {
            "record_id": f"synthetic-{topic}-{index}-a",
            "node_type": "life_event",
            "occurred_on": f"2025-01-{index % 27 + 1:02d}",
            "date_precision": "exact_date",
            "tags": ["migration", "old_role"] if "zhongyin" in topic else ["repeated_pattern"],
            "direction": "supports",
            "magnitude_bp": 1800 + index * 20,
            "source_reliability_bp": 7200,
            "independence_group": f"day-a-{index}",
        },
        {
            "record_id": f"synthetic-{topic}-{index}-b",
            "node_type": "vow",
            "occurred_on": f"2025-03-{index % 27 + 1:02d}",
            "date_precision": "exact_date",
            "tags": ["new_vow", "commitment"],
            "direction": "supports",
            "magnitude_bp": 1500 + index * 15,
            "source_reliability_bp": 7000,
            "independence_group": f"day-b-{index}",
        },
        {
            "record_id": f"synthetic-{topic}-{index}-c",
            "node_type": "relationship",
            "occurred_on": str(2024 - index % 3),
            "date_precision": "year_only",
            "tags": (
                ["subject_deceased_observed", "relationship_echo"]
                if topic == "zhongyin_deceased"
                else ["mutual_response", "unfulfilled_commitment"]
            ),
            "direction": "counters" if index % 4 == 0 else "supports",
            "magnitude_bp": 900 + index * 10,
            "source_reliability_bp": 6500,
            "independence_group": f"day-c-{index}",
            "consent_scope": "bilateral_analysis" if topic == "yuanqi" and index % 2 == 0 else "single_party",
        },
    ]
    if index % 5 == 0:
        facts.append({
            **facts[0],
            "record_id": f"synthetic-{topic}-{index}-duplicate",
            "shared_source_group": facts[0]["record_id"],
        })
        facts[0]["shared_source_group"] = facts[0]["record_id"]
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": f"topic-{topic}-{index:02d}",
        "run_mode": "research_preview",
        "requested_modules": ["signals", "inference"],
        "input_snapshot": {
            "operation": "run_topic_research_v1",
            "topic_type": topic,
            "subject_id": f"synthetic-subject-{index:02d}",
            "relationship_id": f"synthetic-relationship-{index:02d}" if topic == "yuanqi" else None,
            "profile_id": f"synthetic-profile-{index:02d}",
            "facts": facts,
        },
        "ruleset_bundle_id": "topic-research-v1.0.0",
        "data_versions": {
            "tzdb": "2025b",
            "ephemeris": "astronomy-engine/2.1.19",
            "calendar_dataset": "proleptic-gregorian/1.0.0",
        },
        "deterministic_context": {
            "as_of": "2026-07-29T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
        "requested_trace_level": "full",
    }


def main() -> None:
    cases = []
    topics = (
        [("sushe", index) for index in range(1, 25)]
        + [
            ("zhongyin_life" if index <= 12 else "zhongyin_deceased", index)
            for index in range(1, 25)
        ]
        + [("yuanqi", index) for index in range(1, 25)]
    )
    for topic, index in topics:
        engine_request = request(topic, index)
        output = execute(engine_request)
        inference = output["module_results"]["inference"]["result"]
        cases.append({
            "case_id": engine_request["run_id"],
            "asset_class": "synthetic_conformance",
            "request": engine_request,
            "expected": {
                "output_hash": output["output_hash"],
                "trace_hash": output["trace_hash"],
                "result_hash": inference["result_hash"],
                "graph_hash": output["module_results"]["signals"]["result"]["graph"]["graph_hash"],
                "status": inference["status"],
            },
        })
    base = {
        "schema_version": "topic-conformance-cases/1.0.0",
        "asset_class": "synthetic_conformance",
        "reality_validation": False,
        "case_count": len(cases),
        "cases": cases,
    }
    document = {**base, "aggregate_hash": content_hash(base)}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(document["aggregate_hash"])


if __name__ == "__main__":
    main()
