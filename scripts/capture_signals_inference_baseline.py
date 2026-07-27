"""Capture or verify the pre-migration Signals/Inference research baseline.

The fixture is synthetic and is a characterization baseline, not an
authoritative golden sample. Use --write only before changing the legacy
implementation; normal invocation verifies the frozen file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_inference.engine import run_inference, stable_hash

CASES_PATH = ROOT / "tests/fixtures/sprint2-evaluation-cases.json"
CONFIG_PATH = ROOT / "knowledge/research/scoring-config.json"
ARCHETYPES_PATH = ROOT / "knowledge/research/inference-archetypes.json"
BASELINE_PATH = ROOT / "tests/fixtures/signals-inference-research-baseline.json"


def case_payload(spec: dict) -> dict:
    tags = [spec["tag"]] + ([spec["second_tag"]] if spec.get("second_tag") else [])
    signals = []
    for tag_index, tag in enumerate(tags):
        for domain_index, domain in enumerate(("karma", "vow", "dream")):
            signals.append(
                {
                    "id": f"{spec['id']}-{tag_index}-{domain_index}",
                    "domain": domain,
                    "tag": tag,
                    "direction": "support",
                    "strength": 0.8,
                    "source_reliability": 0.8,
                    "relevance": 0.8,
                    "independence_group": f"{spec['id']}-{tag_index}-{domain_index}",
                    "ordinary_explanation_present": spec.get("ordinary", False),
                }
            )
    return {
        "mode": "research_preview",
        "synthetic_or_research": True,
        "random_seed": 42,
        "completeness": spec.get("completeness", 0.9),
        "claim_snapshot": [],
        "signals": signals,
    }


def build_baseline() -> dict:
    cases = json.loads(CASES_PATH.read_text("utf-8"))
    config = json.loads(CONFIG_PATH.read_text("utf-8"))
    archetypes = json.loads(ARCHETYPES_PATH.read_text("utf-8"))
    results = []
    for spec in cases:
        payload = case_payload(spec)
        actual = run_inference(payload, archetypes, config)
        domain_result = {
            "signals": actual["signals"],
            "weights": actual["weights"],
            "locked_verdict": actual["locked_verdict"],
            "locked_hash": actual["locked_hash"],
        }
        results.append(
            {
                "case_id": spec["id"],
                "group": spec["group"],
                "input": payload,
                "input_hash": actual["input_hash"],
                "domain_result": domain_result,
                "domain_result_hash": stable_hash(domain_result),
            }
        )
    aggregate_projection = [
        {"case_id": item["case_id"], "domain_result_hash": item["domain_result_hash"]}
        for item in results
    ]
    return {
        "schema_version": "signals-inference-characterization/1.0.0",
        "baseline_id": "signals-inference-pre-migration-sprint2",
        "baseline_class": "research_baseline",
        "production_activatable": False,
        "case_count": len(results),
        "legacy_engine": "packages.research_inference.engine@0.1.0-research",
        "allowed_exclusions": [
            "notice",
            "persistence_ids",
            "database_generated_ids",
            "runtime_timestamps",
            "local_paths",
            "provider_prose",
        ],
        "aggregate_hash": stable_hash(aggregate_projection),
        "cases": results,
        "disclaimer": (
            "Synthetic migration characterization only; this does not validate "
            "the theory, weights, thresholds, identities, or production use."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    actual = build_baseline()
    if args.write:
        BASELINE_PATH.write_text(
            json.dumps(actual, ensure_ascii=False, indent=2) + "\n", "utf-8"
        )
        print(f"captured {actual['case_count']} cases: {actual['aggregate_hash']}")
        return
    expected = json.loads(BASELINE_PATH.read_text("utf-8"))
    if actual != expected:
        raise SystemExit("signals/inference research baseline drift")
    print(
        f"{actual['case_count']} / {actual['case_count']} equivalent: "
        f"{actual['aggregate_hash']}"
    )


if __name__ == "__main__":
    main()
