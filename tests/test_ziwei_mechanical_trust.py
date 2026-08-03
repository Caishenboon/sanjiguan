from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from sanji_engine import execute, replay
from sanji_engine.canonical import content_hash
from sanji_engine.errors import EngineError
from tests.test_sanji_engine_ziwei import request

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "packages/sanji-engine/src/sanji_engine/ziwei/assets"
REFERENCES = ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/ziwei/mechanical-trust-references-1.0.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def run_case(case: dict, profile_id: str | None = None) -> dict:
    value = case["input"]
    payload = request(profile_id or case["profile_id"])
    payload["run_id"] = f"ziwei-trust-{case['case_id']}-{profile_id or 'primary'}"
    payload["input_snapshot"]["lunar_birth"] = deepcopy(value)
    payload["input_snapshot"]["calendar_provenance"].update(
        historical_legal_time=f"{value['year']:04d}-01-01T00:00:00+08:00",
        user_confirmed=True,
        synthetic=True,
    )
    return execute(payload)


class ZiweiMechanicalTrustTests(unittest.TestCase):
    def test_profiles_are_parallel_unconfirmed_and_without_default(self):
        asset = load(ASSETS / "mechanical-trust-profiles-1.0.0.json")
        self.assertIsNone(asset["default_profile_id"])
        self.assertEqual("UNCONFIRMED", asset["review_status"])
        self.assertFalse(asset["production_activatable"])
        self.assertEqual(2, len(asset["profiles"]))
        self.assertEqual(
            asset["content_hash"],
            content_hash({key: value for key, value in asset.items() if key != "content_hash"}),
        )

    def test_source_evidence_does_not_claim_traditional_authority(self):
        asset = load(ASSETS / "mechanical-source-evidence-1.0.0.json")
        self.assertTrue(all(item["traditional_source"] is None for item in asset["rules"]))
        self.assertTrue(all(item["source_status"] == "UNCONFIRMED" for item in asset["rules"]))
        self.assertEqual(
            asset["content_hash"],
            content_hash({key: value for key, value in asset.items() if key != "content_hash"}),
        )

    def test_independent_reference_projection_matches_engine(self):
        asset = load(REFERENCES)
        self.assertEqual(12, len(asset["cases"]))
        for case in asset["cases"]:
            if case["case_id"] == "profile-leap-divergence":
                primary = run_case(case)["module_results"]["ziwei"]["result"]
                alternate = run_case(case, case["alternate_profile_id"])["module_results"]["ziwei"]["result"]
                self.assertEqual(case["expected"]["primary_decision"], primary["leap_month_decision"])
                self.assertEqual(case["expected"]["alternate_decision"], alternate["leap_month_decision"])
                self.assertNotEqual(primary["profile_hash"], alternate["profile_hash"])
                continue
            result = run_case(case)["module_results"]["ziwei"]["result"]
            expected = case["expected"]
            self.assertEqual(expected["life_palace_branch"], result["life_palace"]["branch"], case["case_id"])
            self.assertEqual(expected["body_palace_branch"], result["body_palace"]["branch"], case["case_id"])
            self.assertEqual(expected["five_element_bureau"], result["five_element_bureau"]["name"], case["case_id"])
            star_map = {item["name"]: item["branch"] for item in result["fourteen_major_stars"]}
            self.assertEqual(expected["major_star_map_hash"], content_hash(star_map), case["case_id"])

    def test_reference_hash_is_separate_and_canonical(self):
        asset = load(REFERENCES)
        self.assertEqual(asset["aggregate_hash"], content_hash(asset["cases"]))
        self.assertEqual(
            asset["content_hash"],
            content_hash({key: value for key, value in asset.items() if key != "content_hash"}),
        )

    def test_manual_input_fail_closed_boundaries(self):
        for field, value in (("month", 0), ("month", 13), ("day", 0), ("day", 31), ("hour_branch_index", -1), ("hour_branch_index", 12)):
            payload = request()
            payload["input_snapshot"]["lunar_birth"][field] = value
            with self.assertRaises(EngineError):
                execute(payload)
        missing = request()
        del missing["input_snapshot"]["lunar_birth"]["hour_branch_index"]
        with self.assertRaises(EngineError):
            execute(missing)

    def test_reference_replay_and_order_invariance(self):
        case = load(REFERENCES)["cases"][0]
        first_request = request(case["profile_id"])
        first_request["input_snapshot"]["lunar_birth"] = deepcopy(case["input"])
        first = execute(first_request)
        reordered = deepcopy(first_request)
        reordered["input_snapshot"]["lunar_birth"] = dict(reversed(list(reordered["input_snapshot"]["lunar_birth"].items())))
        second = execute(reordered)
        self.assertEqual(first["output_hash"], second["output_hash"])
        self.assertEqual(first["trace_hash"], second["trace_hash"])
        replayed = replay(first["replay_manifest"], first_request)
        self.assertEqual(first["output_hash"], replayed["output_hash"])


if __name__ == "__main__":
    unittest.main()
