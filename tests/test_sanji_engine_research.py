import json
import unittest
from copy import deepcopy
from pathlib import Path

from sanji_engine import execute, inspect_ruleset, replay
from sanji_engine.canonical import content_hash
from sanji_engine.errors import EngineError

ROOT = Path(__file__).resolve().parents[1]
BASELINE = json.loads(
    (ROOT / "tests/fixtures/signals-inference-research-baseline.json").read_text("utf-8")
)


def encode(value):
    if isinstance(value, float):
        return str(value)
    if isinstance(value, dict):
        return {key: encode(child) for key, child in value.items()}
    if isinstance(value, list):
        return [encode(child) for child in value]
    return value


def request_for(case, bundle_id="research-baseline-0.2.0", mode="research_preview"):
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": "research-contract-test",
        "run_mode": mode,
        "requested_modules": ["signals", "inference"],
        "input_snapshot": {
            "operation": "run_research_inference",
            "case": encode(case),
        },
        "ruleset_bundle_id": bundle_id,
        "data_versions": {
            "tzdb": "not_used",
            "ephemeris": "not_used",
            "calendar_dataset": "not_used",
            "research_archetypes": "0.1.0-research",
            "research_scoring": "0.1.0-research",
        },
        "deterministic_context": {
            "as_of": "2000-01-01T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
    }


class SanjiEngineResearchTests(unittest.TestCase):
    def setUp(self):
        self.case = deepcopy(BASELINE["cases"][0]["input"])

    def assert_code(self, code, request):
        with self.assertRaises(EngineError) as raised:
            execute(request)
        self.assertEqual(code, raised.exception.code)

    def test_ruleset_is_research_only(self):
        bundle = inspect_ruleset("research-baseline-0.2.0")
        self.assertEqual("research_active", bundle["status"])
        self.assertFalse(bundle["production_activatable"])
        for module in ("signals", "inference"):
            self.assertEqual("research_baseline", bundle["modules"][module]["baseline_class"])
            self.assertFalse(bundle["modules"][module]["production_activatable"])

    def test_cross_platform_hash_order_status_trace_and_replay(self):
        fixture = json.loads(
            (
                ROOT
                / "packages/sanji-engine/src/sanji_engine/golden_cases/"
                "research_baseline/cross-platform-1.json"
            ).read_text("utf-8")
        )
        result = execute(request_for(self.case))
        expected = fixture["expected"]
        self.assertEqual(expected["output_hash"], result["output_hash"])
        self.assertEqual(expected["trace_hash"], result["trace_hash"])
        self.assertEqual(
            expected["research_domain_hash"],
            result["replay_manifest"]["domain_result_hashes"]["research_domain_hash"],
        )
        locked = result["module_results"]["inference"]["result"]["locked_verdict"]
        self.assertEqual(expected["verdict"], locked["verdict"])
        self.assertEqual(
            sorted(
                locked["ranked_hypotheses"],
                key=lambda item: (-float(item["raw_score"]), item["id"]),
            ),
            locked["ranked_hypotheses"],
        )
        self.assertEqual(result["output_hash"], replay(result["replay_manifest"], request_for(self.case))["output_hash"])
        self.assertEqual(
            ["signals:100:validate_and_deduplicate_signals",
             "inference:200:generate_and_score_candidates",
             "inference:300:rank_and_decide_status"],
            [step["step_id"] for step in result["trace"]],
        )

    def test_signal_validation_boundaries(self):
        invalid_cases = []
        missing_source = deepcopy(self.case)
        missing_source["signals"][0].pop("independence_group")
        invalid_cases.append(missing_source)
        invalid_direction = deepcopy(self.case)
        invalid_direction["signals"][0]["direction"] = "neutral"
        invalid_cases.append(invalid_direction)
        invalid_ratio = deepcopy(self.case)
        invalid_ratio["signals"][0]["source_reliability"] = "1.1"
        invalid_cases.append(invalid_ratio)
        duplicate = deepcopy(self.case)
        duplicate["signals"].append(deepcopy(duplicate["signals"][0]))
        invalid_cases.append(duplicate)
        unknown_domain = deepcopy(self.case)
        unknown_domain["signals"][0]["domain"] = "unknown"
        invalid_cases.append(unknown_domain)
        for case in invalid_cases:
            self.assert_code("INPUT_INVALID", request_for(case))

    def test_independence_group_dedup_and_empty_input(self):
        case = deepcopy(self.case)
        duplicate = deepcopy(case["signals"][0])
        duplicate["id"] = "same-group-weaker"
        duplicate["strength"] = 0.1
        case["signals"].append(duplicate)
        result = execute(request_for(case))
        signals = result["module_results"]["signals"]["result"]
        self.assertNotIn("same-group-weaker", [item["id"] for item in signals["signals"]])
        empty = deepcopy(self.case)
        empty["signals"] = []
        empty_result = execute(request_for(empty))
        locked = empty_result["module_results"]["inference"]["result"]["locked_verdict"]
        # Frozen legacy behavior: completeness, not an empty Signal list, is the
        # insufficiency gate. This surprising result is documented technical debt.
        self.assertEqual("contested", locked["verdict"])

    def test_support_counterevidence_hard_and_soft_conflict_characterization(self):
        oppose = deepcopy(self.case)
        oppose["signals"][0]["direction"] = "oppose"
        opposed = execute(request_for(oppose))
        ranked = opposed["module_results"]["inference"]["result"]["locked_verdict"]["ranked_hypotheses"]
        self.assertTrue(
            any(
                contribution["value"].startswith("-")
                for item in ranked
                for contribution in item["contributions"]
            )
        )

        hard = deepcopy(self.case)
        hard["signals"].extend(
            [
                {
                    "id": "healing-signal",
                    "domain": "karma",
                    "tag": "healing",
                    "direction": "support",
                    "strength": 1,
                    "source_reliability": 1,
                    "relevance": 1,
                    "independence_group": "healing",
                },
                {
                    "id": "medical-conflict",
                    "domain": "vow",
                    "tag": "medical_fabrication",
                    "direction": "support",
                    "strength": 1,
                    "source_reliability": 1,
                    "relevance": 1,
                    "independence_group": "medical-conflict",
                },
            ]
        )
        locked = execute(request_for(hard))["module_results"]["inference"]["result"]["locked_verdict"]
        healing = next(item for item in locked["ranked_hypotheses"] if item["id"] == "AR.RESEARCH.HEALING")
        self.assertEqual(["medical_fabrication"], healing["hard_conflicts"])

        contested = deepcopy(self.case)
        for signal in contested["signals"]:
            signal["tag"] = "caregiving"
        contested_locked = execute(request_for(contested))["module_results"]["inference"]["result"]["locked_verdict"]
        self.assertEqual("contested", contested_locked["verdict"])

    def test_replay_mismatch_and_asset_failures(self):
        result = execute(request_for(self.case))
        manifest = result["replay_manifest"]

        changed_input = deepcopy(self.case)
        changed_input["completeness"] = 0.8
        with self.assertRaises(EngineError) as raised:
            replay(manifest, request_for(changed_input))
        self.assertEqual("REPLAY_INPUT_MISMATCH", raised.exception.code)

        changed_data = request_for(self.case)
        changed_data["data_versions"]["research_scoring"] = "other"
        with self.assertRaises(EngineError) as raised:
            replay(manifest, changed_data)
        self.assertEqual("REPLAY_DATA_VERSION_MISMATCH", raised.exception.code)

        bad_method = deepcopy(manifest)
        bad_method["method_versions"]["inference"] = "INFERENCE.OTHER"
        bad_method["content_hash"] = content_hash(
            {key: value for key, value in bad_method.items() if key != "content_hash"}
        )
        with self.assertRaises(EngineError) as raised:
            replay(bad_method, request_for(self.case))
        self.assertEqual("REPLAY_METHOD_VERSION_MISMATCH", raised.exception.code)

        bad_result = deepcopy(manifest)
        bad_result["domain_result_hashes"]["research_domain_hash"] = "sha256:" + "0" * 64
        bad_result["content_hash"] = content_hash(
            {key: value for key, value in bad_result.items() if key != "content_hash"}
        )
        with self.assertRaises(EngineError) as raised:
            replay(bad_result, request_for(self.case))
        self.assertEqual("REPLAY_RESULT_MISMATCH", raised.exception.code)

        missing = request_for(self.case)
        missing["ruleset_bundle_id"] = "missing-ruleset"
        self.assert_code("RULESET_NOT_FOUND", missing)

    def test_revoked_ruleset_replay_only(self):
        revoked_id = "research-baseline-0.2.0-revoked-fixture"
        self.assert_code("RULESET_REVOKED", request_for(self.case, revoked_id))
        historical = execute(request_for(self.case, revoked_id, "replay"))
        replayed = replay(
            historical["replay_manifest"],
            request_for(self.case, revoked_id, "research_preview"),
        )
        self.assertEqual(historical["output_hash"], replayed["output_hash"])


if __name__ == "__main__":
    unittest.main()
