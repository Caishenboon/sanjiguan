import itertools
import json
import unittest
from copy import deepcopy
from pathlib import Path

from lunar_python.util import LunarUtil
from sanji_engine import execute, replay, validate_request
from sanji_engine.bazi.traditional_structure import (
    BRANCHES, HIDDEN_STEMS, HIDDEN_STEMS_PROFILE_LUNAR_PYTHON,
    HIDDEN_STEMS_PROFILE_PRIMARY, HIDDEN_STEM_PROFILES, METHOD_ID,
    PROFILE_ID, STEMS, ten_god,
    _branch_relations, _stem_relations,
)
from sanji_engine.canonical import content_hash
from sanji_engine.errors import EngineError

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/bazi/traditional-structure-mechanical-reference-v1.json"


def request_for(pillars=None, hidden_profile=HIDDEN_STEMS_PROFILE_PRIMARY, run_id="bazi-structure-test"):
    return {
        "schema_version": "engine-request/1.0.0", "engine_api_version": "1.0",
        "run_id": run_id, "run_mode": "research_preview", "requested_modules": ["bazi"],
        "input_snapshot": {
            "operation": "calculate_bazi_traditional_structure",
            "profile_id": PROFILE_ID, "profile_version": "1.0.0",
            "hidden_stems_profile_id": hidden_profile,
            "source_four_pillars": pillars or {
                "year": {"stem": "甲", "branch": "子"}, "month": {"stem": "己", "branch": "巳"},
                "day": {"stem": "甲", "branch": "申"}, "hour": {"stem": "庚", "branch": "辰"},
            },
            "source_candidate_id": "synthetic-candidate-001",
            "source_ruleset_id": "bazi-four-pillars-research-1.0.0",
            "source_method_id": "BAZI.FOUR_PILLARS.MECHANICAL.RESEARCH.V1",
            "source_method_version": "1.0.0",
            "month_context": {"solar_month_index": 4, "boundary_sensitive": False},
        },
        "ruleset_bundle_id": "bazi-traditional-structure-research-1.0.0",
        "data_versions": {
            "tzdb": "2025.2", "ephemeris": "astronomy-engine/2.1.19",
            "calendar_dataset": "calendar-migration-baseline-1.0.0",
            "bazi_method_profiles": "bazi-traditional-structure-profiles/1.0.0",
            "bazi_traditional_structure": "bazi-traditional-structure-assets/1.0.0",
        },
        "deterministic_context": {"as_of": "2000-01-01T00:00:00Z", "random_method": "none", "random_seed": None},
    }


def result_for(request):
    return execute(request)["module_results"]["bazi"]["result"]


class BaziTraditionalStructureTests(unittest.TestCase):
    def test_reference_is_explicitly_non_authoritative_and_counted(self):
        data = json.loads(REFERENCE.read_text(encoding="utf-8"))
        self.assertEqual("mechanical_reference", data["classification"])
        self.assertEqual("NOT_AUTHORITY_GOLDEN", data["authority_status"])
        self.assertEqual(166, sum(group["case_count"] for group in data["case_groups"]))
        self.assertEqual(166, data["declared_case_count"])

    def test_all_hidden_stems_match_independent_implementation_with_explicit_si_dispute(self):
        reference = json.loads(REFERENCE.read_text(encoding="utf-8"))["reference_tables"]
        for branch in BRANCHES:
            actual = [stem for stem, _ in HIDDEN_STEM_PROFILES[HIDDEN_STEMS_PROFILE_LUNAR_PYTHON][branch]]
            self.assertEqual(LunarUtil.ZHI_HIDE_GAN[branch], actual)
            self.assertEqual(reference["hidden_stems_lunar_python_comparison_profile"][branch], actual)
            self.assertEqual(reference["hidden_stems_primary_profile"][branch], [stem for stem, _ in HIDDEN_STEMS[branch]])
        self.assertNotEqual(HIDDEN_STEMS["巳"], HIDDEN_STEM_PROFILES[HIDDEN_STEMS_PROFILE_LUNAR_PYTHON]["巳"])
        self.assertEqual(("丙", "戊", "庚"), tuple(stem for stem, _ in HIDDEN_STEMS["巳"]))
        with self.assertRaises(EngineError):
            request = request_for()
            request["input_snapshot"].pop("hidden_stems_profile_id")
            execute(request)

    def test_all_100_ten_god_pairs_match_independent_implementation(self):
        matrix = json.loads(REFERENCE.read_text(encoding="utf-8"))["reference_tables"]["ten_gods_matrix"]
        pairs = list(itertools.product(STEMS, repeat=2))
        self.assertEqual(100, len(pairs))
        for day_stem, target_stem in pairs:
            with self.subTest(day=day_stem, target=target_stem):
                self.assertEqual(LunarUtil.SHI_SHEN[day_stem + target_stem], ten_god(day_stem, target_stem))
                self.assertEqual(matrix[day_stem][STEMS.index(target_stem)], ten_god(day_stem, target_stem))

    def test_unknown_hour_is_not_fabricated_and_month_command_is_not_strength(self):
        request = request_for()
        request["input_snapshot"]["source_four_pillars"]["hour"] = None
        result = result_for(request)
        self.assertEqual(["hour_pillar"], result["missing"])
        self.assertIsNone(result["pillars"]["hour"])
        self.assertIsNone(result["month_command"]["strength_conclusion"])
        self.assertNotIn("hour", {item["position"] for item in result["hidden_stems"]})

    def test_relations_are_candidates_without_formation_or_interpretation(self):
        pillars = {
            "year": {"stem": "甲", "branch": "申"}, "month": {"stem": "己", "branch": "子"},
            "day": {"stem": "丙", "branch": "辰"}, "hour": {"stem": "辛", "branch": "申"},
        }
        result = result_for(request_for(pillars))
        stem = {item["relation"]: item for item in result["stem_relations"]}
        self.assertFalse(stem["five_combine"]["transformation_determined"])
        branch = [item for item in result["branch_relations"] if item["relation"] == "three_harmony"]
        self.assertEqual(1, len(branch))
        self.assertFalse(branch[0]["formation_determined"])
        self.assertIsNone(result["interpretation"])
        self.assertIn("strength", result["not_implemented"])

    def test_all_reference_relation_catalogs_are_detected(self):
        tables = json.loads(REFERENCE.read_text(encoding="utf-8"))["reference_tables"]
        for pair in tables["stem_five_combines"]:
            pillars = {"year":{"stem":pair[0],"branch":"子"}, "month":{"stem":pair[1],"branch":"丑"}, "day":{"stem":"丙","branch":"寅"}, "hour":None}
            matches = [item for item in _stem_relations(pillars) if item["relation"] == "five_combine" and {x["position"] for x in item["participants"]} == {"year", "month"}]
            self.assertEqual(1, len(matches), pair)
            self.assertFalse(matches[0]["transformation_determined"])
        for relation, pairs in tables["branch_pair_catalog"].items():
            for pair in pairs:
                pillars = {"year":{"stem":"甲","branch":pair[0]}, "month":{"stem":"乙","branch":pair[1]}, "day":{"stem":"丙","branch":"寅"}, "hour":None}
                matches = [item for item in _branch_relations(pillars) if item["relation"] == relation and {x["position"] for x in item["participants"]} == {"year", "month"}]
                self.assertEqual(1, len(matches), (relation, pair))
        for relation, groups in tables["three_member_catalog"].items():
            for group in groups:
                pillars = {position:{"stem":"甲","branch":branch} for position, branch in zip(("year","month","day"), group)}
                pillars["hour"] = None
                matches = [item for item in _branch_relations(pillars) if item["relation"] == relation]
                self.assertEqual(1, len(matches), (relation, group))
                self.assertFalse(matches[0]["formation_determined"])

    def test_position_and_input_order_are_canonical_and_hash_stable(self):
        first = request_for()
        second = deepcopy(first)
        second["input_snapshot"]["source_four_pillars"] = dict(reversed(list(second["input_snapshot"]["source_four_pillars"].items())))
        one = execute(first)
        two = execute(second)
        self.assertEqual(one["output_hash"], two["output_hash"])
        self.assertEqual(one["trace_hash"], two["trace_hash"])

    def test_replay_preserves_profile_result_and_hash(self):
        request = request_for()
        first = execute(request)
        replayed = replay(first["replay_manifest"], request)
        self.assertEqual(first["output_hash"], replayed["output_hash"])
        self.assertEqual(first["module_results"]["bazi"]["result"]["result_hash"], replayed["module_results"]["bazi"]["result"]["result_hash"])
        self.assertEqual(METHOD_ID, replayed["module_results"]["bazi"]["result"]["method_id"])

    def test_reference_asset_has_stable_new_aggregate_hash(self):
        data = json.loads(REFERENCE.read_text(encoding="utf-8"))
        self.assertEqual("sha256:a81019a737762808cb29636b06753cbcf18582d968be107df428287f7463f25b", content_hash(data))


if __name__ == "__main__":
    unittest.main()
