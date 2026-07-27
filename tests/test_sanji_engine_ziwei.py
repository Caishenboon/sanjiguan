from __future__ import annotations

from copy import deepcopy
import unittest

from sanji_engine import execute, replay
from sanji_engine.errors import EngineError
from sanji_engine.ziwei.mechanical import BRANCHES, calculate_chart


def request(profile_id: str = "ZIWEI.SANHE.MANUAL_LUNAR.LEAP_SAME_MONTH.V1") -> dict:
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": "synthetic-ziwei-001",
        "run_mode": "research_preview",
        "requested_modules": ["ziwei"],
        "input_snapshot": {
            "operation": "calculate_ziwei_chart",
            "profile_id": profile_id,
            "profile_version": "1.0.0",
            "lunar_birth": {
                "year": 2000,
                "month": 1,
                "day": 1,
                "is_leap_month": False,
                "hour_branch_index": 0,
                "traditional_sex": "male",
            },
            "calendar_provenance": {
                "conversion_method": "manual_verified_lunar_input",
                "timezone_id": "Asia/Shanghai",
                "historical_legal_time": "2000-02-05T00:30:00+08:00",
                "user_confirmed": True,
                "synthetic": True,
            },
            "target_year": 2026,
        },
        "ruleset_bundle_id": "ziwei-sanhe-research-1.0.0",
        "data_versions": {
            "tzdb": "2025.2",
            "ephemeris": "astronomy-engine/2.1.19",
            "calendar_dataset": "manual-lunar/1.0.0",
            "ziwei_profiles": "ziwei-profile-registry/1.0.0",
            "ziwei_transformations": "birth-year-transformations-candidate/1.0.0",
            "ziwei_source_claims": "ziwei-source-claim-registry/1.0.0",
        },
        "deterministic_context": {
            "as_of": "2026-07-27T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
        "requested_trace_level": "full",
    }


class ZiweiMechanicalTests(unittest.TestCase):
    def test_reference_chart_is_complete_research_only_and_replayable(self):
        result = execute(request())
        domain = result["module_results"]["ziwei"]["result"]
        self.assertEqual({"branch": "寅", "index": 2}, domain["life_palace"])
        self.assertEqual({"branch": "寅", "index": 2}, domain["body_palace"])
        self.assertEqual("土五局", domain["five_element_bureau"]["name"])
        self.assertEqual(12, len(domain["twelve_palaces"]))
        self.assertEqual(14, len(domain["fourteen_major_stars"]))
        self.assertEqual(4, len(domain["birth_year_transformations"]))
        self.assertEqual(12, len(domain["decade_cycles"]))
        self.assertIsNone(domain["interpretation"])
        self.assertEqual("UNCONFIRMED", domain["review_status"])
        self.assertFalse(domain["production_activatable"])
        self.assertEqual(
            "sha256:225d8d9b12662339af41882ade7ec73532190c50edadc66aec392e08a3abff27",
            result["output_hash"],
        )
        self.assertEqual(
            "sha256:81462bbe1a63f045c1176a115dd285889bc7b61a5c2b00c622fbd236de1c2cb7",
            result["trace_hash"],
        )
        self.assertEqual(
            "sha256:ea42ff4f7f4455f66f60183b70aa6bfc8919243a295b1495b1707746352e430e",
            result["replay_manifest"]["domain_result_hashes"]["ziwei_domain_hash"],
        )
        replayed = replay(result["replay_manifest"], request())
        self.assertEqual(result["output_hash"], replayed["output_hash"])

    def test_all_months_and_hours_have_one_life_and_body_palace(self):
        for month in range(1, 13):
            for hour in range(12):
                snapshot = request()["input_snapshot"]
                snapshot["lunar_birth"]["month"] = month
                snapshot["lunar_birth"]["hour_branch_index"] = hour
                domain, trace, _ = calculate_chart(snapshot)
                self.assertIn(domain["life_palace"]["branch"], BRANCHES)
                self.assertIn(domain["body_palace"]["branch"], BRANCHES)
                self.assertEqual(9, len(trace))

    def test_all_five_bureaus_and_fourteen_stars_are_reachable_and_complete(self):
        bureaus = set()
        for year in range(1990, 2002):
            for month in range(1, 13):
                snapshot = request()["input_snapshot"]
                snapshot["lunar_birth"].update(year=year, month=month, day=17)
                domain, _, _ = calculate_chart(snapshot)
                bureaus.add(domain["five_element_bureau"]["name"])
                self.assertEqual(
                    14, len({item["name"] for item in domain["fourteen_major_stars"]})
                )
        self.assertEqual({"水二局", "木三局", "金四局", "土五局", "火六局"}, bureaus)

    def test_leap_profiles_expose_difference_without_defaulting(self):
        same = request()
        same["input_snapshot"]["lunar_birth"].update(
            month=4, day=20, is_leap_month=True
        )
        split = deepcopy(same)
        split["run_id"] = "synthetic-ziwei-002"
        split["input_snapshot"]["profile_id"] = "ZIWEI.SANHE.MANUAL_LUNAR.LEAP_SPLIT_15.V1"
        a = execute(same)["module_results"]["ziwei"]["result"]
        b = execute(split)["module_results"]["ziwei"]["result"]
        self.assertEqual("leap_same_month", a["leap_month_decision"])
        self.assertEqual("leap_split_second_half_next_month", b["leap_month_decision"])
        self.assertNotEqual(a["profile_hash"], b["profile_hash"])

    def test_missing_profile_and_unverified_conversion_fail_closed(self):
        missing = request()
        del missing["input_snapshot"]["profile_id"]
        with self.assertRaises(EngineError):
            execute(missing)
        automatic = request()
        automatic["input_snapshot"]["calendar_provenance"]["conversion_method"] = "automatic"
        with self.assertRaises(EngineError):
            execute(automatic)

    def test_revoked_ruleset_rejects_new_execution(self):
        revoked = request()
        revoked["ruleset_bundle_id"] = "ziwei-sanhe-research-1.0.0-revoked-fixture"
        with self.assertRaises(EngineError) as raised:
            execute(revoked)
        self.assertEqual("RULESET_REVOKED", raised.exception.code)
