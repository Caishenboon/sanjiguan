from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from sanji_engine import execute, replay
from sanji_engine.canonical import content_hash
from sanji_engine.errors import EngineError

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / (
    "packages/sanji-engine/src/sanji_engine/golden_cases/topics/"
    "topic-conformance-v1.json"
)


def _load() -> dict:
    return json.loads(CASES.read_text(encoding="utf-8"))


def _inference(output: dict) -> dict:
    return output["module_results"]["inference"]["result"]


class TopicEngineV1Tests(unittest.TestCase):
    def test_all_72_synthetic_conformance_cases_are_frozen(self) -> None:
        asset = _load()
        self.assertEqual(asset["asset_class"], "synthetic_conformance")
        self.assertFalse(asset["reality_validation"])
        self.assertEqual(asset["case_count"], 72)
        for case in asset["cases"]:
            output = execute(case["request"])
            inference = _inference(output)
            expected = case["expected"]
            self.assertEqual(output["output_hash"], expected["output_hash"])
            self.assertEqual(output["trace_hash"], expected["trace_hash"])
            self.assertEqual(inference["result_hash"], expected["result_hash"])
            self.assertEqual(
                output["module_results"]["signals"]["result"]["graph"]["graph_hash"],
                expected["graph_hash"],
            )
            self.assertEqual(inference["status"], expected["status"])
        base = {key: value for key, value in asset.items() if key != "aggregate_hash"}
        self.assertEqual(content_hash(base), asset["aggregate_hash"])

    def test_sushe_names_are_nonempty_unique_and_replay_stable(self) -> None:
        case = next(item for item in _load()["cases"] if item["case_id"].startswith("topic-sushe"))
        output = execute(case["request"])
        candidates = _inference(output)["candidates"]
        names = [item["name"]["value"] for item in candidates]
        self.assertEqual(len(candidates), 3)
        self.assertTrue(all(name and name not in {"未知", "无名氏"} for name in names))
        self.assertEqual(len(set(names)), 3)
        self.assertTrue(all(item["name"]["epistemic_status"] == "generated_identity" for item in candidates))
        self.assertTrue(all(item["candidate_output_hash"].startswith("sha256:") for item in candidates))
        self.assertTrue(all(item["trace_hash"].startswith("sha256:") for item in candidates))
        replayed = replay(output["replay_manifest"], case["request"])
        self.assertEqual(replayed["output_hash"], output["output_hash"])
        self.assertEqual(
            [item["name"]["value"] for item in _inference(replayed)["candidates"]],
            names,
        )

    def test_low_confidence_still_has_specific_sushe_names(self) -> None:
        request = deepcopy(_load()["cases"][0]["request"])
        request["run_id"] = "low-confidence-name"
        request["input_snapshot"]["facts"] = request["input_snapshot"]["facts"][:1]
        inference = _inference(execute(request))
        self.assertEqual(inference["status"], "insufficient")
        self.assertTrue(all(item["name"]["value"] for item in inference["candidates"]))
        self.assertTrue(all(item["name"]["confidence_bp"] < 5000 for item in inference["candidates"]))

    def test_input_order_and_shared_source_duplicates_do_not_change_result(self) -> None:
        request = deepcopy(_load()["cases"][4]["request"])
        first = execute(request)
        request["run_id"] = "order-change"
        request["input_snapshot"]["facts"].reverse()
        second = execute(request)
        self.assertEqual(first["input_hash"], second["input_hash"])
        self.assertEqual(first["output_hash"], second["output_hash"])
        self.assertTrue(any(
            item["discounted_record_ids"]
            for item in second["module_results"]["signals"]["result"]["deduplication"]
        ))

    def test_deceased_mode_requires_observed_deceased_tag(self) -> None:
        request = deepcopy(_load()["cases"][24]["request"])
        request["run_id"] = "deceased-gate"
        request["input_snapshot"]["topic_type"] = "zhongyin_deceased"
        with self.assertRaises(EngineError) as caught:
            execute(request)
        self.assertEqual(caught.exception.details["code"], "deceased_subject_required")

    def test_bardo_never_predicts_future_death(self) -> None:
        for case in [item for item in _load()["cases"] if "zhongyin" in item["case_id"]]:
            candidate = _inference(execute(case["request"]))["candidates"][0]
            self.assertTrue(candidate["no_future_death_prediction"])
            self.assertNotIn("death_time", candidate)
            self.assertNotIn("lifespan", candidate)

    def test_yuanqi_consent_boundary_and_generated_names(self) -> None:
        cases = [item for item in _load()["cases"] if "yuanqi" in item["case_id"]]
        unilateral = _inference(execute(cases[0]["request"]))["candidates"][0]
        bilateral = _inference(execute(cases[1]["request"]))["candidates"][0]
        self.assertEqual(unilateral["observation_scope"], "single_party_relationship_observation")
        self.assertIn("bilateral_analysis_consent", unilateral["missing_facts"])
        self.assertEqual(bilateral["observation_scope"], "bilateral_structure")
        self.assertTrue(all(item["name"]["value"] for item in unilateral["past_life_identity_candidates"]))
        self.assertFalse(unilateral["destined_partner_claim"])
        self.assertFalse(unilateral["absolute_reunion_claim"])

    def test_external_model_inputs_are_rejected(self) -> None:
        for forbidden in ("deepseek", "llm", "oracle", "embedding"):
            request = deepcopy(_load()["cases"][0]["request"])
            request["run_id"] = f"forbidden-{forbidden}"
            request["input_snapshot"][forbidden] = {"enabled": False}
            with self.assertRaises(EngineError):
                execute(request)

    def test_no_unlicensed_historical_person_is_emitted(self) -> None:
        for candidate in _inference(execute(_load()["cases"][0]["request"]))["candidates"]:
            self.assertEqual(candidate["historical_person_candidates"], [])
            self.assertEqual(candidate["name_type"], "deterministic_generated_identity")


if __name__ == "__main__":
    unittest.main()
