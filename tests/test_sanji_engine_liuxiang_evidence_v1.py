from __future__ import annotations

import json
import unittest
from copy import deepcopy
from importlib.resources import files

from sanji_engine import execute, replay
from sanji_engine.canonical import content_hash
from sanji_engine.signals.evidence_v1 import run_liuxiang_evidence_v1


def request(snapshot: dict, run_id: str = "evidence-test") -> dict:
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": run_id,
        "run_mode": "research_preview",
        "requested_modules": ["signals", "inference"],
        "input_snapshot": snapshot,
        "ruleset_bundle_id": "liuxiang-evidence-research-v1.0.0",
        "data_versions": {
            "tzdb": "2025.2",
            "ephemeris": "astronomy-engine/2.1.19",
            "calendar_dataset": "calendar-baseline/1.0.0",
        },
        "deterministic_context": {
            "as_of": "2026-07-29T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
        "requested_trace_level": "full",
    }


class LiuxiangEvidenceV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.asset = json.loads(
            files("sanji_engine").joinpath(
                "golden_cases/liuxiang/user-evidence-conformance-v1.json"
            ).read_text(encoding="utf-8")
        )

    def test_seventy_two_synthetic_cases_and_aggregate_hash(self):
        self.assertEqual(72, len(self.asset["cases"]))
        hashes = []
        for case in self.asset["cases"]:
            result, trace = run_liuxiang_evidence_v1(case["snapshot"])
            self.assertEqual(case["expected_status"], result["status"])
            self.assertEqual(case["result_hash"], result["result_hash"])
            self.assertEqual(case["trace_hash"], content_hash(trace))
            hashes.append({
                "case_id": case["case_id"],
                "result_hash": result["result_hash"],
                "trace_hash": content_hash(trace),
            })
        self.assertEqual(self.asset["aggregate_hash"], content_hash(hashes))

    def test_coverage_never_increases_strength_but_can_raise_confidence(self):
        base = deepcopy(self.asset["cases"][14]["snapshot"])
        without, _ = run_liuxiang_evidence_v1(base)
        coverage = deepcopy(base["facts"][0])
        coverage.update({
            "record_id": "coverage-extra",
            "fact_kind": "coverage",
            "direction": "neutral",
            "coverage_fields": {"record_available": True},
        })
        base["facts"].append(coverage)
        with_coverage, _ = run_liuxiang_evidence_v1(base)
        self.assertEqual(without["strength_bp"], with_coverage["strength_bp"])
        self.assertGreaterEqual(with_coverage["confidence_bp"], without["confidence_bp"])

    def test_duplicate_multi_tag_same_day_and_withdrawal_do_not_inflate(self):
        cases = {case["scenario"]: case for case in self.asset["cases"] if case["dimension_id"] == "lx_ye"}
        baseline, _ = run_liuxiang_evidence_v1(cases["cross_date_independent"]["snapshot"])
        duplicate, _ = run_liuxiang_evidence_v1(cases["duplicate_record_tags"]["snapshot"])
        self.assertEqual(baseline["strength_bp"], duplicate["strength_bp"])
        withdrawn, _ = run_liuxiang_evidence_v1(cases["withdrawn"]["snapshot"])
        excluded, _ = run_liuxiang_evidence_v1(cases["excluded"]["snapshot"])
        self.assertEqual(baseline["strength_bp"], withdrawn["strength_bp"])
        self.assertEqual(baseline["strength_bp"], excluded["strength_bp"])
        same_day, _ = run_liuxiang_evidence_v1(cases["same_day_cap"]["snapshot"])
        self.assertLessEqual(same_day["strength_bp"], baseline["strength_bp"])

    def test_two_descriptions_of_one_event_share_one_effective_source(self):
        case = deepcopy(next(
            case for case in self.asset["cases"]
            if case["dimension_id"] == "lx_ye" and case["scenario"] == "cross_date_independent"
        ))
        first = case["snapshot"]["facts"][0]
        duplicate_description = deepcopy(first)
        duplicate_description.update({
            "record_id": "lx_ye:description:two",
            "occurred_on": "2026-01-02",
            "shared_source_group": "event:one-observed-event",
        })
        first["shared_source_group"] = "event:one-observed-event"
        with_duplicate, _ = run_liuxiang_evidence_v1(case["snapshot"] | {
            "facts": [*case["snapshot"]["facts"], duplicate_description]
        })
        without_duplicate, _ = run_liuxiang_evidence_v1(case["snapshot"])
        self.assertEqual(without_duplicate["strength_bp"], with_duplicate["strength_bp"])
        self.assertEqual(
            without_duplicate["candidates"][0]["independent_evidence_count"],
            with_duplicate["candidates"][0]["independent_evidence_count"],
        )

    def test_one_behavior_and_one_vow_are_not_high_strength(self):
        behavior = next(case for case in self.asset["cases"] if case["dimension_id"] == "lx_ye" and case["scenario"] == "single_record")
        vow = next(case for case in self.asset["cases"] if case["dimension_id"] == "lx_yuan" and case["scenario"] == "single_record")
        self.assertEqual(0, run_liuxiang_evidence_v1(behavior["snapshot"])[0]["strength_bp"])
        self.assertLess(run_liuxiang_evidence_v1(vow["snapshot"])[0]["strength_bp"], 1000)

    def test_dream_requires_confirmed_tags_and_has_no_fortune_field(self):
        case = deepcopy(next(
            case for case in self.asset["cases"]
            if case["dimension_id"] == "lx_meng" and case["scenario"] == "cross_date_independent"
        ))
        tagged, _ = run_liuxiang_evidence_v1(case["snapshot"])
        for fact in case["snapshot"]["facts"]:
            fact["confirmed_tags"] = []
        untagged, _ = run_liuxiang_evidence_v1(case["snapshot"])
        self.assertGreater(tagged["strength_bp"], untagged["strength_bp"])
        self.assertNotIn("fortune", json.dumps(tagged))

    def test_single_party_relationship_never_becomes_mutual(self):
        case = deepcopy(next(
            case for case in self.asset["cases"]
            if case["dimension_id"] == "lx_yuan_relation" and case["scenario"] == "cross_date_independent"
        ))
        for fact in case["snapshot"]["facts"]:
            fact["relationship_confirmation"] = "single_party"
        result, _ = run_liuxiang_evidence_v1(case["snapshot"])
        self.assertNotIn("mutual", json.dumps(result))

    def test_year_precision_is_preserved(self):
        case = next(
            case for case in self.asset["cases"]
            if case["dimension_id"] == "lx_shi" and case["scenario"] == "precision_preserved"
        )
        result, _ = run_liuxiang_evidence_v1(case["snapshot"])
        signal = next(
            item for item in result["signals"]
            if item["source_record_id"].endswith("record:4")
        )
        self.assertEqual({"occurred_on": "2024", "date_precision": "year_only"}, signal["temporal_scope"])

    def test_order_invariance_and_replay(self):
        snapshot = deepcopy(self.asset["cases"][26]["snapshot"])
        original = execute(request(snapshot, "original"))
        snapshot["facts"].reverse()
        reordered = execute(request(snapshot, "reordered"))
        self.assertEqual(original["output_hash"], reordered["output_hash"])
        reproduced = replay(original["replay_manifest"], request(
            deepcopy(self.asset["cases"][26]["snapshot"]), "replay"
        ))
        self.assertEqual(original["output_hash"], reproduced["output_hash"])

    def test_oracle_llm_and_interpretive_fields_are_rejected(self):
        snapshot = deepcopy(self.asset["cases"][14]["snapshot"])
        snapshot["facts"][0]["llm_score"] = 9999
        with self.assertRaises(ValueError):
            run_liuxiang_evidence_v1(snapshot)

    def test_boundary_and_profile_dispute_reduce_confidence(self):
        cases = {case["scenario"]: case for case in self.asset["cases"] if case["dimension_id"] == "lx_ye"}
        no_penalty = deepcopy(cases["boundary_sensitive"]["snapshot"])
        no_penalty["facts"][-1]["boundary_sensitivity_bp"] = 0
        baseline = run_liuxiang_evidence_v1(no_penalty)[0]
        boundary = run_liuxiang_evidence_v1(cases["boundary_sensitive"]["snapshot"])[0]
        no_dispute = deepcopy(cases["profile_dispute"]["snapshot"])
        no_dispute["facts"][-1]["profile_dispute_bp"] = 0
        dispute_baseline = run_liuxiang_evidence_v1(no_dispute)[0]
        dispute = run_liuxiang_evidence_v1(cases["profile_dispute"]["snapshot"])[0]
        self.assertLessEqual(boundary["confidence_bp"], baseline["confidence_bp"])
        self.assertLessEqual(dispute["confidence_bp"], dispute_baseline["confidence_bp"])
