import ast
import json
import unittest
from copy import deepcopy
from pathlib import Path

from sanji_engine import execute, inspect_ruleset, validate_request
from sanji_engine.bazi import (
    ConformanceError,
    compare_profiles,
    list_profiles,
    load_boundary_cases,
    load_evidence_bundle,
    load_profile,
    run_conformance,
    validate_profile,
)
from sanji_engine.errors import EngineError

from tests.test_sanji_engine_core import deterministic_request

ROOT = Path(__file__).resolve().parents[1]
PROFILE_IDS = [item["profile_id"] for item in list_profiles()]


class BaziMethodConformanceTests(unittest.TestCase):
    def test_profile_schema_fields_and_research_states(self):
        expected_fields = {
            "profile_id", "profile_version", "status", "production_activatable",
            "calendar_basis", "legal_time_policy", "solar_time_mode",
            "year_boundary_policy", "month_boundary_policy",
            "day_rollover_policy", "hour_boundary_policy",
            "boundary_inclusion_policy", "historical_calendar_policy",
            "unknown_time_policy", "location_precision_policy",
            "source_claim_ids", "review_status", "reviewer_requirements",
            "known_disputes", "content_hash",
        }
        self.assertEqual(3, len(PROFILE_IDS))
        for profile_id in PROFILE_IDS:
            profile = load_profile(profile_id)
            self.assertTrue(expected_fields <= set(profile))
            self.assertIn(profile["status"], {"draft", "review_candidate"})
            self.assertFalse(profile["production_activatable"])
            self.assertEqual("UNCONFIRMED", profile["review_status"])
            self.assertEqual(
                "CANDIDATE_ONLY_NOT_OWNER_DECISION",
                profile["selection_authority"],
            )

    def test_missing_fields_invalid_status_and_production_gate(self):
        profile = load_profile(PROFILE_IDS[0])
        missing = deepcopy(profile)
        missing.pop("day_rollover_policy")
        with self.assertRaisesRegex(ConformanceError, "incomplete"):
            validate_profile(missing)

        invalid = deepcopy(profile)
        invalid["status"] = "production_active"
        invalid["content_hash"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ConformanceError, "research-safe"):
            validate_profile(invalid)

        unsafe = deepcopy(profile)
        unsafe["production_activatable"] = True
        unsafe["content_hash"] = "sha256:" + "0" * 64
        with self.assertRaises(ConformanceError) as captured:
            validate_profile(unsafe)
        self.assertEqual("PRODUCTION_GATE", captured.exception.code)

    def test_evidence_claim_and_locator_integrity(self):
        evidence = load_evidence_bundle()
        self.assertEqual(12, len(evidence["claims"]))
        self.assertEqual(10, len(evidence["locators"]))
        locator_ids = {item["locator_id"] for item in evidence["locators"]}
        claim_ids = {item["claim_id"] for item in evidence["claims"]}
        for claim in evidence["claims"]:
            self.assertTrue(set(claim["locator_ids"]) <= locator_ids)
            self.assertTrue(set(claim["supports_claim_ids"]) <= claim_ids)
            self.assertTrue(set(claim["contradicts_claim_ids"]) <= claim_ids)
        self.assertTrue(
            any(not item["review_candidate_ready"] for item in evidence["claims"])
        )

    def test_boundary_asset_counts_hashes_and_unique_ids(self):
        asset = load_boundary_cases()
        self.assertEqual(74, asset["case_count"])
        self.assertEqual(
            {
                "time_and_timezone": 8,
                "year_boundary": 4,
                "month_boundary": 38,
                "day_boundary": 7,
                "hour_boundary": 17,
            },
            asset["category_counts"],
        )
        case_ids = [item["case_id"] for item in asset["cases"]]
        self.assertEqual(len(case_ids), len(set(case_ids)))
        self.assertTrue(all(item["input"]["synthetic"] for item in asset["cases"]))
        self.assertTrue(all(item["expected_difference"]["pillar_values"] is None
                            for item in asset["cases"]))

    def test_profile_difference_detection_and_canonical_hash(self):
        comparison = compare_profiles(PROFILE_IDS)
        self.assertFalse(comparison["calculation_performed"])
        self.assertIsNone(comparison["pillar_results"])
        self.assertEqual(
            {"solar_time_mode", "day_rollover_policy", "hour_boundary_policy"},
            set(comparison["differences"]),
        )
        first = run_conformance(PROFILE_IDS)
        second = run_conformance(list(reversed(PROFILE_IDS)))
        self.assertNotEqual(first["content_hash"], second["content_hash"])
        repeat = run_conformance(PROFILE_IDS)
        self.assertEqual(first["content_hash"], repeat["content_hash"])
        self.assertEqual(
            {
                "mechanically_verified", "profile_discriminating",
                "source_attested", "pending_manual_review",
            },
            set(load_boundary_cases()["classification_definitions"]),
        )

    def test_missing_profile_unknown_case_and_profile_mismatch_are_distinct(self):
        with self.assertRaises(ConformanceError) as missing_profile:
            run_conformance([])
        self.assertEqual("DATA_MISSING", missing_profile.exception.code)

        with self.assertRaises(ConformanceError) as missing_case:
            run_conformance(PROFILE_IDS, ["NOT-A-CASE"])
        self.assertEqual("DATA_MISSING", missing_case.exception.code)

        with self.assertRaises(ConformanceError) as duplicate:
            compare_profiles([PROFILE_IDS[0], PROFILE_IDS[0]])
        self.assertEqual("PROFILE_MISMATCH", duplicate.exception.code)

    def test_engine_requires_explicit_profile_and_stays_disabled(self):
        request = deterministic_request()
        request["ruleset_bundle_id"] = "bazi-method-foundation-0.1.0"
        validated = validate_request(request)
        self.assertEqual(
            "BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1",
            validated["input_snapshot"]["bazi_method_profile_id"],
        )
        result = execute(request)
        bazi = result["module_results"]["bazi"]
        self.assertEqual("MODULE_DISABLED", bazi["error"]["code"])
        self.assertIsNone(bazi["result"])

        missing = deepcopy(request)
        missing["input_snapshot"].pop("bazi_method_profile_id")
        with self.assertRaisesRegex(EngineError, "explicit method profile"):
            validate_request(missing)

    def test_ruleset_inspection_exposes_profiles_without_activation(self):
        bundle = inspect_ruleset("bazi-method-foundation-0.1.0")
        bazi = bundle["modules"]["bazi"]
        self.assertEqual("review_candidate", bazi["status"])
        self.assertFalse(bazi["enabled"])
        self.assertFalse(bazi["production_activatable"])
        self.assertEqual("MODULE_DISABLED", bazi["execution_result"])
        self.assertEqual(set(PROFILE_IDS), set(bazi["profile_ids"]))

    def test_cross_platform_fixture(self):
        result = run_conformance(PROFILE_IDS)
        fixture = json.loads(
            (
                ROOT
                / "packages/sanji-engine/src/sanji_engine/golden_cases/bazi/"
                "method-conformance-cross-platform-1.json"
            ).read_text("utf-8")
        )
        self.assertEqual(fixture["expected_content_hash"], result["content_hash"])
        self.assertEqual(
            fixture["boundary_asset_hash"],
            load_boundary_cases()["content_hash"],
        )

    def test_bazi_package_contains_no_pillar_algorithm(self):
        bazi_root = (
            ROOT / "packages/sanji-engine/src/sanji_engine/bazi"
        )
        forbidden_functions = {
            "calculate_year_pillar",
            "calculate_month_pillar",
            "calculate_day_pillar",
            "calculate_hour_pillar",
            "calculate_ten_gods",
            "calculate_strength",
            "calculate_luck_cycles",
        }
        found = set()
        for path in bazi_root.rglob("*.py"):
            tree = ast.parse(path.read_text("utf-8"))
            found.update(
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
        self.assertFalse(found & forbidden_functions)


if __name__ == "__main__":
    unittest.main()
