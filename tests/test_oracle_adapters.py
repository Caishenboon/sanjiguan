from __future__ import annotations

import unittest
import platform
import json
from pathlib import Path

from oracle_adapters import (
    diff_against_engine,
    execute_oracle,
    identify_oracle,
    inspect_oracle,
)
from sanji_engine import execute
from tests.test_sanji_engine_ziwei import request as ziwei_request
from tests.test_sanji_engine_bazi_four_pillars import (
    PROFILES,
    birth_record,
    request_for as bazi_request,
)


class OracleAdapterTests(unittest.TestCase):
    def test_complete_bazi_differential_matrix_is_exercised(self):
        matrix = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "packages/oracle-adapters/fixtures/bazi-differential-matrix.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(10, len(matrix["cases"]))
        self.assertEqual(3, len(matrix["profiles"]))
        self.assertEqual(3, len(matrix["oracles"]))
        attempts = 0
        for case in matrix["cases"]:
            for profile_id in matrix["profiles"]:
                oracle_input = {
                    key: case[key]
                    for key in (
                        "local_date",
                        "local_time",
                        "timezone_id",
                        "time_resolution_status",
                    )
                    if key in case
                }
                oracle_input["profile_id"] = profile_id
                if case.get("time_resolution_status"):
                    expected_execution = "unsupported"
                elif case["local_time"] is None:
                    expected_execution = "unsupported"
                else:
                    expected_execution = "success"
                engine = None
                if expected_execution == "success":
                    engine = execute(
                        bazi_request(
                            profile_id,
                            birth_record(
                                case["local_date"],
                                case["local_time"],
                                timezone_id=case["timezone_id"],
                            ),
                            run_id=f"oracle-matrix-{case['case_id']}-{profile_id}",
                        )
                    )
                for oracle_id in matrix["oracles"]:
                    with self.subTest(case=case["case_id"], profile=profile_id, oracle=oracle_id):
                        result = execute_oracle(oracle_id, oracle_input)
                        attempts += 1
                        if oracle_id == "bazi.sxtwl" and platform.system() != "Linux":
                            self.assertIn(result["execution_status"], {expected_execution, "unsupported"})
                        else:
                            self.assertEqual(expected_execution, result["execution_status"])
                        if engine is not None:
                            diff = diff_against_engine(result, engine)
                            self.assertFalse(diff["affects_engine_result"])
        self.assertEqual(90, attempts)

    def test_registry_is_pinned_non_production_and_does_not_touch_user_data(self):
        for oracle_id in (
            "bazi.lunar_python",
            "bazi.tyme4py",
            "bazi.sxtwl",
            "ziwei.iztro",
        ):
            identity = identify_oracle(oracle_id)
            self.assertTrue(identity["oracle_version"])
            self.assertTrue(identity["license"])
            inspected = inspect_oracle(oracle_id)
            self.assertFalse(inspected["production_allowed"])
            self.assertFalse(inspected["touches_user_data"])
            self.assertFalse(inspected["affects_engine_determinism"])

    def test_iztro_normalizes_and_matches_synthetic_reference(self):
        oracle = execute_oracle(
            "ziwei.iztro",
            {
                "lunar_year": 2000,
                "lunar_month": 1,
                "lunar_day": 1,
                "hour_index": 0,
                "traditional_sex": "male",
                "profile_id": "ZIWEI.SANHE.MANUAL_LUNAR.LEAP_SAME_MONTH.V1",
            },
        )
        self.assertEqual("success", oracle["execution_status"])
        diff = diff_against_engine(oracle, execute(ziwei_request()))
        self.assertEqual("normalized_match", diff["status"])
        self.assertFalse(diff["affects_engine_result"])

    def test_iztro_matches_all_versioned_mechanical_references(self):
        references = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "packages/sanji-engine/src/sanji_engine/golden_cases/ziwei/mechanical-trust-references-1.0.0.json"
            ).read_text(encoding="utf-8")
        )
        compared = 0
        for case in references["cases"]:
            if case["comparison_status"] != "NORMALIZED_MATCH":
                continue
            value = case["input"]
            engine_request = ziwei_request(case["profile_id"])
            engine_request["run_id"] = f"oracle-trust-{case['case_id']}"
            engine_request["input_snapshot"]["lunar_birth"] = value
            oracle = execute_oracle(
                "ziwei.iztro",
                {
                    "lunar_year": value["year"],
                    "lunar_month": value["month"],
                    "lunar_day": value["day"],
                    "hour_index": value["hour_branch_index"],
                    "traditional_sex": value["traditional_sex"],
                    "profile_id": case["profile_id"],
                },
            )
            diff = diff_against_engine(oracle, execute(engine_request))
            self.assertEqual("normalized_match", diff["status"], case["case_id"])
            self.assertFalse(diff["affects_engine_result"])
            compared += 1
        self.assertEqual(10, compared)

    def test_unknown_oracle_is_rejected(self):
        with self.assertRaises(ValueError):
            identify_oracle("unknown")

    def test_three_bazi_oracles_are_differential_only_across_three_profiles(self):
        for profile_id in PROFILES:
            engine = execute(
                bazi_request(
                    profile_id,
                    birth_record("2024-07-01", "12:00:00"),
                    run_id=f"oracle-{profile_id}",
                )
            )
            for oracle_id in (
                "bazi.lunar_python",
                "bazi.tyme4py",
                "bazi.sxtwl",
            ):
                oracle = execute_oracle(oracle_id, {
                    "local_date": "2024-07-01",
                    "local_time": "12:00:00",
                    "profile_id": profile_id,
                })
                if oracle_id == "bazi.sxtwl" and platform.system() != "Linux":
                    self.assertIn(oracle["execution_status"], {"success", "unsupported"})
                else:
                    self.assertEqual("success", oracle["execution_status"])
                diff = diff_against_engine(oracle, engine)
                self.assertIn(diff["status"], {
                    "exact_match", "profile_difference",
                    "manual_review_required", "unsupported",
                })
                self.assertFalse(diff["affects_engine_result"])

    def test_unknown_birth_time_is_explicitly_unsupported(self):
        result = execute_oracle("bazi.lunar_python", {
            "local_date": "2024-07-01",
            "local_time": None,
            "profile_id": PROFILES[0],
        })
        self.assertEqual("unsupported", result["execution_status"])
        self.assertEqual(["unknown_birth_time"], result["unsupported_features"])
