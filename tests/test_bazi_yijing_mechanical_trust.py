from __future__ import annotations

import json
import platform
import unittest
from copy import deepcopy
from pathlib import Path

from sanji_engine import execute
from sanji_engine.canonical import content_hash
from sanji_engine.errors import EngineError
from tests.test_sanji_engine_bazi_four_pillars import birth_record, request_for
from tests.test_sanji_engine_yijing import request_for as yijing_request

ROOT = Path(__file__).resolve().parents[1]
BAZI_ASSETS = ROOT / "packages/sanji-engine/src/sanji_engine/bazi/assets"
YIJING_ASSETS = ROOT / "packages/sanji-engine/src/sanji_engine/yijing/assets"
GOLDENS = ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/bazi/mechanical-trust-goldens-1.0.0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def _pillar_names(candidate: dict) -> dict:
    return {key: value["ganzhi"] for key, value in candidate["pillars"].items()}


class MechanicalTrustTests(unittest.TestCase):
    def test_profiles_are_parallel_research_assets_without_hidden_default(self):
        asset = _load(BAZI_ASSETS / "mechanical-trust-profiles-1.0.0.json")
        self.assertEqual("research_active", asset["activation_status"])
        self.assertEqual("UNCONFIRMED", asset["review_status"])
        self.assertFalse(asset["production_activatable"])
        self.assertIsNone(asset["default_profile_id"])
        self.assertEqual(3, len(asset["parallel_disputed_profiles"]))
        self.assertEqual(
            asset["content_hash"],
            content_hash({key: value for key, value in asset.items() if key != "content_hash"}),
        )

    def test_day_epoch_evidence_does_not_promote_unconfirmed_anchor(self):
        asset = _load(BAZI_ASSETS / "day-epoch-evidence-1.0.0.json")
        assessment = asset["source_assessment"]
        self.assertEqual("CONSENSUS_MECHANICAL", assessment["jdn_source_status"])
        self.assertEqual("UNCONFIRMED", assessment["sexagenary_anchor_source_status"])
        self.assertEqual("RESEARCH_ONLY", assessment["production_status"])
        self.assertIn("was not replaced or promoted", asset["conclusion"])
        self.assertEqual(
            asset["content_hash"],
            content_hash({key: value for key, value in asset.items() if key != "content_hash"}),
        )

    def test_engine_matches_separately_versioned_mechanical_references(self):
        asset = _load(GOLDENS)
        self.assertEqual(13, len(asset["cases"]))
        for case in asset["cases"]:
            item = case["input"]
            record = birth_record(
                item["local_date"], item["local_time"], timezone_id=item["timezone_id"]
            )
            record["place"]["longitude"] = item["longitude"]
            try:
                result = execute(request_for(case["profile_id"], record, case["case_id"]))
            except EngineError as exc:
                self.assertEqual(case["expected"].get("error_code"), exc.code, case["case_id"])
                continue
            domain = result["module_results"]["bazi"]["result"]
            expected = case["expected"]
            if "pillars" in expected:
                self.assertEqual(expected["pillars"], _pillar_names(domain["candidates"][0]), case["case_id"])
            if "candidate_pillars" in expected:
                actual = [
                    {"track_id": value["track_id"], "pillars": _pillar_names(value)}
                    for value in domain["candidates"]
                ]
                self.assertEqual(expected["candidate_pillars"], actual, case["case_id"])
            for key in ("candidate_count", "four_pillars", "missing_data"):
                if key in expected:
                    self.assertEqual(expected[key], domain[key], case["case_id"])

    def test_golden_hash_is_separate_and_canonical(self):
        asset = _load(GOLDENS)
        cases_hash = content_hash(asset["cases"])
        self.assertEqual(cases_hash, asset["aggregate_hash"])
        body = {key: value for key, value in asset.items() if key != "content_hash"}
        self.assertEqual(asset["content_hash"], content_hash(body))

    @unittest.skipUnless(platform.system() == "Linux", "sxtwl binary comparison is Linux CI only")
    def test_truly_independent_sxtwl_ordinary_case(self):
        from oracle_adapters import execute_oracle

        case = _load(GOLDENS)["cases"][0]
        oracle = execute_oracle("bazi.sxtwl", {
            "local_date": case["input"]["local_date"],
            "local_time": case["input"]["local_time"],
            "profile_id": case["profile_id"],
        })
        self.assertEqual("success", oracle["execution_status"])
        self.assertEqual(case["expected"]["pillars"], oracle["normalized_result"]["pillars"])

    def test_coin_value_contract_is_numeric_and_labels_are_secondary(self):
        asset = _load(YIJING_ASSETS / "coin-value-profile-1.0.0.json")
        contract = asset["canonical_contract"]
        self.assertEqual([2, 3], contract["allowed_single_coin_values"])
        self.assertEqual("bottom_to_top", contract["input_order"])
        self.assertEqual({"6", "7", "8", "9"}, set(contract["line_sums"]))
        self.assertEqual("profile_interpretation_not_canonical_identity", asset["face_label_profile"]["status"])
        self.assertEqual("unchanged", asset["historical_compatibility"]["direct_line_values_6_7_8_9"])
        self.assertFalse(asset["historical_compatibility"]["canonical_result_hash_changes"])
        self.assertEqual(
            asset["content_hash"],
            content_hash({key: value for key, value in asset.items() if key != "content_hash"}),
        )

    def test_all_coin_combinations_and_line_order_attack(self):
        states = {}
        for a in (2, 3):
            for b in (2, 3):
                for c in (2, 3):
                    request = yijing_request((7,) * 6)
                    request["input_snapshot"]["tosses"][0]["coin_values"] = [a, b, c]
                    result = execute(request)["module_results"]["yijing"]["result"]
                    line = result["lines"][0]
                    states.setdefault(a + b + c, set()).add(
                        (line["line_state"], line["moving"], line["base_polarity"], line["transformed_polarity"])
                    )
        self.assertEqual({6, 7, 8, 9}, set(states))
        self.assertTrue(all(len(value) == 1 for value in states.values()))

        reversed_request = yijing_request((6, 7, 8, 9, 7, 8))
        reversed_request["input_snapshot"]["tosses"] = list(reversed(reversed_request["input_snapshot"]["tosses"]))
        with self.assertRaises(EngineError) as raised:
            execute(reversed_request)
        self.assertEqual("INPUT_INVALID", raised.exception.code)

    def test_zero_one_many_moving_and_4096_regression(self):
        moving_counts = {}
        aggregate = []
        for index in range(4096):
            values = tuple(6 + ((index >> (position * 2)) & 3) for position in range(6))
            result = execute(yijing_request(values))
            domain = result["module_results"]["yijing"]["result"]
            moving_counts.setdefault(len(domain["moving_lines"]), 0)
            moving_counts[len(domain["moving_lines"])] += 1
            aggregate.append((domain["base_hexagram"]["key"], tuple(domain["moving_lines"]), domain["transformed_hexagram"]["key"]))
        self.assertIn(0, moving_counts)
        self.assertIn(1, moving_counts)
        self.assertTrue(any(count > 1 for count in moving_counts))
        self.assertEqual(4096, len(set(aggregate)))


if __name__ == "__main__":
    unittest.main()
