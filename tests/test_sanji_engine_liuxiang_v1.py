from __future__ import annotations

import json
import unittest
from copy import deepcopy
from importlib.resources import files

from sanji_engine import execute, replay
from sanji_engine.canonical import content_hash
from sanji_engine.errors import EngineError
from sanji_engine.inference.liuxiang_v1 import run_liuxiang_research_v1
from sanji_engine.signals.adapters import adapt_mechanical_facts


def request(case: dict, run_id: str = "liuxiang-test") -> dict:
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": run_id,
        "run_mode": "research_preview",
        "requested_modules": ["signals", "inference"],
        "input_snapshot": case["snapshot"],
        "ruleset_bundle_id": "liuxiang-research-v1.0.0",
        "data_versions": {
            "tzdb": "2025.2",
            "ephemeris": "astronomy-engine/2.1.19",
            "calendar_dataset": "calendar-baseline/1.0.0",
        },
        "deterministic_context": {
            "as_of": "2026-07-28T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
        "requested_trace_level": "full",
    }


class LiuxiangV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.asset = json.loads(
            files("sanji_engine").joinpath(
                "golden_cases/liuxiang/synthetic-conformance-v1.json"
            ).read_text(encoding="utf-8")
        )

    def test_one_hundred_synthetic_cases_and_aggregate_hash(self):
        self.assertEqual(100, len(self.asset["cases"]))
        hashes = []
        for case in self.asset["cases"]:
            result, _ = run_liuxiang_research_v1(case["snapshot"])
            self.assertEqual(case["expected_status"], result["status"], case["case_id"])
            hashes.append({"case_id": case["case_id"], "result_hash": result["result_hash"]})
        self.assertEqual(self.asset["aggregate_hash"], content_hash(hashes))

    def test_order_invariance_and_replay(self):
        case = deepcopy(self.asset["cases"][0])
        original = execute(request(case, "original"))
        case["snapshot"]["signals"].reverse()
        reordered = execute(request(case, "reordered"))
        self.assertEqual(original["output_hash"], reordered["output_hash"])
        replayed = replay(original["replay_manifest"], request(self.asset["cases"][0], "replay"))
        self.assertEqual(original["output_hash"], replayed["output_hash"])

    def test_same_source_does_not_increase_strength_or_confidence(self):
        case = deepcopy(self.asset["cases"][3])
        result, _ = run_liuxiang_research_v1(case["snapshot"])
        one = deepcopy(case)
        one["snapshot"]["signals"] = one["snapshot"]["signals"][:1]
        single, _ = run_liuxiang_research_v1(one["snapshot"])
        self.assertEqual(result["strength_bp"], single["strength_bp"])
        self.assertEqual(result["confidence_bp"], single["confidence_bp"])

    def test_strength_and_confidence_are_separate(self):
        result, _ = run_liuxiang_research_v1(self.asset["cases"][7]["snapshot"])
        self.assertGreaterEqual(result["strength_bp"], 9000)
        self.assertLess(result["confidence_bp"], 7000)
        self.assertEqual("provisional", result["status"])

    def test_monotonic_support_counterevidence_and_completeness(self):
        decisive = deepcopy(self.asset["cases"][0])
        one = deepcopy(decisive)
        one["snapshot"]["signals"] = one["snapshot"]["signals"][:1]
        one_result, _ = run_liuxiang_research_v1(one["snapshot"])
        full_result, _ = run_liuxiang_research_v1(decisive["snapshot"])
        self.assertGreaterEqual(full_result["strength_bp"], one_result["strength_bp"])
        counter = deepcopy(one)
        opposition = deepcopy(counter["snapshot"]["signals"][0])
        opposition.update({
            "signal_id": "counter:independent",
            "source_record_id": "counter:record",
            "source_fact_path": "$.counter",
            "direction": "negative",
            "independence_group": "counter:independent",
            "shared_source_group": "counter:source",
            "supports": [],
            "counterevidence": ["lx_ming"],
            "trace_ref": "counter:trace",
        })
        counter["snapshot"]["signals"].append(opposition)
        counter_result, _ = run_liuxiang_research_v1(counter["snapshot"])
        self.assertLessEqual(counter_result["strength_bp"], one_result["strength_bp"])
        low_complete = deepcopy(one)
        low_complete["snapshot"]["completeness_bp_by_dimension"]["lx_ming"] = 4000
        low_result, _ = run_liuxiang_research_v1(low_complete["snapshot"])
        self.assertGreaterEqual(one_result["confidence_bp"], low_result["confidence_bp"])

    def test_profile_boundary_and_evidence_withdrawal_reduce_confidence_or_strength(self):
        baseline = deepcopy(self.asset["cases"][0])
        base_result, _ = run_liuxiang_research_v1(baseline["snapshot"])
        profile = deepcopy(baseline)
        boundary = deepcopy(baseline)
        for signal in profile["snapshot"]["signals"]:
            signal["disputes"]["penalty_bp"] = 8000
        for signal in boundary["snapshot"]["signals"]:
            signal["boundary_sensitivity"]["penalty_bp"] = 8000
        profile_result, _ = run_liuxiang_research_v1(profile["snapshot"])
        boundary_result, _ = run_liuxiang_research_v1(boundary["snapshot"])
        self.assertLess(profile_result["confidence_bp"], base_result["confidence_bp"])
        self.assertLess(boundary_result["confidence_bp"], base_result["confidence_bp"])
        withdrawn = deepcopy(baseline)
        withdrawn["snapshot"]["signals"].pop()
        withdrawn_result, _ = run_liuxiang_research_v1(withdrawn["snapshot"])
        self.assertNotEqual(base_result["result_hash"], withdrawn_result["result_hash"])
        self.assertLessEqual(withdrawn_result["strength_bp"], base_result["strength_bp"])

    def test_fixed_cross_platform_hash_fixture(self):
        result = execute(request(self.asset["cases"][0], "cross-platform-fixture"))
        self.assertEqual(
            "sha256:fa7154b90d3373c9f1c42068bd70abebdd10b2df111a07050d0af8658c797430",
            result["output_hash"],
        )
        self.assertEqual(
            "sha256:e77862036f9a46596a02e68da438f62a3464e3cffc405f66065ec67da23d9017",
            result["trace_hash"],
        )

    def test_ruleset_and_operation_cannot_be_cross_wired(self):
        wrong = request(self.asset["cases"][0], "wrong-ruleset")
        wrong["ruleset_bundle_id"] = "research-baseline-0.2.0"
        with self.assertRaises(EngineError):
            execute(wrong)

    def test_disabled_or_cross_sourced_mapping_cannot_generate_signal(self):
        disabled = deepcopy(self.asset["cases"][0]["snapshot"])
        disabled["signals"][0]["mapping_rule_id"] = "LX.BAZI.MECHANICAL.CANDIDATE.V1"
        with self.assertRaises(EngineError):
            run_liuxiang_research_v1(disabled)
        cross_sourced = deepcopy(self.asset["cases"][0]["snapshot"])
        cross_sourced["signals"][0]["source_system"] = "bazi"
        with self.assertRaises(EngineError):
            run_liuxiang_research_v1(cross_sourced)

    def test_mechanical_adapters_extract_only_allowlisted_facts(self):
        for system, result in {
            "yijing": {"lines": [6, 7, 8, 9, 7, 8], "interpretation": "forbidden"},
            "bazi": {"pillars": {"year": "synthetic"}, "strength": "forbidden"},
            "ziwei": {"life_palace": "synthetic", "fortune": "forbidden"},
        }.items():
            facts = adapt_mechanical_facts(system, result, "profile-v1")
            serialized = json.dumps(facts, ensure_ascii=False)
            self.assertNotIn("forbidden", serialized)
            self.assertTrue(all(value["content_hash"].startswith("sha256:") for value in facts))

    def test_oracle_and_llm_fields_are_rejected(self):
        case = deepcopy(self.asset["cases"][0]["snapshot"])
        case["oracle_vote"] = "different"
        first, _ = run_liuxiang_research_v1(case)
        case["oracle_vote"] = "another"
        case["deepseek_text"] = "not consumed"
        second, _ = run_liuxiang_research_v1(case)
        self.assertEqual(first["result_hash"], second["result_hash"])


if __name__ == "__main__":
    unittest.main()
