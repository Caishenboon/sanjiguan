import json
import unittest
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

from jsonschema import Draft202012Validator
from sanji_engine import execute, inspect_ruleset, replay, validate_request
from sanji_engine.bazi.conformance import load_boundary_cases
from sanji_engine.bazi.four_pillars import (
    BRANCHES, JIE, STEMS, _day_index, _jie_for_year, _pillar,
)
from sanji_engine.bazi.profiles import day_epoch_asset, execution_profile_registry
from sanji_engine.errors import EngineError

ROOT = Path(__file__).resolve().parents[1]
PROFILES = (
    "BAZI.PROFILE.CIVIL_MIDNIGHT.CANDIDATE.V1",
    "BAZI.PROFILE.APPARENT_ZICHU.CANDIDATE.V1",
    "BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1",
)


def birth_record(local_date="2024-01-01", local_time="12:00:00", **updates):
    value = {
        "local_date": local_date,
        "local_time": local_time,
        "calendar_type": "gregorian",
        "time_precision": "second" if local_time is not None else "unknown",
        "timezone_id": "Asia/Shanghai",
        "place": {
            "latitude": "31.230400",
            "longitude": "121.473700",
            "name": "Synthetic",
            "precision": "exact_test_coordinate",
        },
        "user_confirmed": True,
    }
    value.update(updates)
    return value


def request_for(profile_id=PROFILES[0], record=None, run_id="bazi-test"):
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": run_id,
        "run_mode": "research_preview",
        "requested_modules": ["bazi"],
        "input_snapshot": {
            "operation": "calculate_bazi_four_pillars",
            "profile_id": profile_id,
            "profile_version": "1.0.0",
            "birth_record": record or birth_record(),
            "input_provenance": {
                "local_date": "synthetic_fixture",
                "local_time": "synthetic_fixture",
                "timezone_id": "synthetic_fixture",
                "coordinates": "synthetic_fixture",
            },
        },
        "ruleset_bundle_id": "bazi-four-pillars-research-1.0.0",
        "data_versions": {
            "tzdb": "2025.2",
            "ephemeris": "astronomy-engine/2.1.19",
            "calendar_dataset": "calendar-migration-baseline-1.0.0",
            "bazi_method_profiles": "bazi-execution-profiles/1.0.0",
            "bazi_day_epoch": "bazi-day-epoch/1.0.0",
            "bazi_boundary_cases": "bazi-boundary-cases/1.0.0",
            "solar_terms": "astronomy-engine/2.1.19",
        },
        "deterministic_context": {
            "as_of": "2000-01-01T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
    }


def domain(request):
    return execute(request)["module_results"]["bazi"]["result"]


class BaziFourPillarsTests(unittest.TestCase):
    def test_profile_and_version_are_both_required_without_default(self):
        for field in ("profile_id", "profile_version"):
            request = request_for()
            request["input_snapshot"].pop(field)
            with self.subTest(field=field), self.assertRaises(EngineError) as raised:
                validate_request(request)
            self.assertEqual("INPUT_INVALID", raised.exception.code)
        registry = execution_profile_registry()
        self.assertEqual(3, len(registry["profiles"]))
        self.assertFalse(registry["production_activatable"])
        self.assertEqual("UNCONFIRMED", registry["review_status"])
        self.assertNotIn("default_profile_id", registry)

    def test_three_profiles_execute_and_preserve_declared_policy(self):
        record = birth_record("1990-02-11", "23:30:00")
        results = {profile: domain(request_for(profile, record)) for profile in PROFILES}
        for profile, result in results.items():
            self.assertEqual(profile, result["profile"]["profile_id"])
            self.assertEqual("1.0.0", result["profile"]["profile_version"])
            self.assertEqual("research_active", result["research_status"])
            self.assertEqual("UNCONFIRMED", result["review_status"])
            self.assertFalse(result["production_activatable"])
            self.assertIsNone(result["interpretation"])
            self.assertIsNone(result["auspiciousness"])
        self.assertEqual(1, results[PROFILES[0]]["candidate_count"])
        self.assertEqual(1, results[PROFILES[1]]["candidate_count"])
        self.assertEqual(2, results[PROFILES[2]]["candidate_count"])
        civil_day = results[PROFILES[0]]["candidates"][0]["pillars"]["day"]["ganzhi"]
        apparent_day = results[PROFILES[1]]["candidates"][0]["pillars"]["day"]["ganzhi"]
        self.assertNotEqual(civil_day, apparent_day)

    def test_apparent_correction_crossing_lichun_is_explicit_not_silent(self):
        record = birth_record("2024-02-04", "16:30:00")
        civil = domain(request_for(PROFILES[0], record))["candidates"][0]
        apparent = domain(request_for(PROFILES[1], record))["candidates"][0]
        self.assertEqual("甲辰", civil["pillars"]["year"]["ganzhi"])
        self.assertEqual("癸卯", apparent["pillars"]["year"]["ganzhi"])
        self.assertEqual("丙寅", civil["pillars"]["month"]["ganzhi"])
        self.assertEqual("乙丑", apparent["pillars"]["month"]["ganzhi"])
        self.assertTrue(apparent["boundary_flags"]["solar_correction_crosses_year_boundary"])
        self.assertTrue(apparent["boundary_flags"]["solar_correction_crosses_month_boundary"])
        self.assertEqual(
            "local_apparent_solar",
            apparent["pillars"]["year"]["comparison_basis"],
        )
        self.assertNotEqual(
            apparent["time_calculation_chain"]["user_local_civil"],
            apparent["time_calculation_chain"]["selected_by_pillar"]["year"]["datetime"],
        )

    def test_year_cycle_month_stem_cycle_day_cycle_and_hour_cycle(self):
        reference = json.loads((
            ROOT / "packages/sanji-engine/src/sanji_engine/bazi/assets/"
            "mechanical-reference-tables-1.0.0.json"
        ).read_text("utf-8"))
        self.assertEqual(
            reference["sexagenary_cycle"],
            [_pillar(index)["ganzhi"] for index in range(60)],
        )
        self.assertEqual(
            reference["sexagenary_cycle"],
            [_pillar(index + 60)["ganzhi"] for index in range(60)],
        )
        years = [
            domain(request_for(record=birth_record(f"{year}-07-01")))["four_pillars"]["year"]
            for year in range(1984, 2044)
        ]
        self.assertEqual(60, len({item["ganzhi"] for item in years}))
        start = date(2024, 1, 1)
        days = [_day_index(start + timedelta(days=offset))[0] for offset in range(61)]
        self.assertEqual(list(range(60)), days[:60])
        self.assertEqual(days[0], days[60])
        for year_stem in range(10):
            month_stems = [
                ((year_stem % 5) * 2 + 2 + month_index) % 10
                for month_index in range(12)
            ]
            self.assertEqual(12, len(month_stems))
            self.assertEqual(
                reference["yin_month_start_stem_by_year_stem"][STEMS[year_stem]],
                STEMS[month_stems[0]],
            )
        for day_stem in range(10):
            hour_stems = [((day_stem % 10) * 2 + branch) % 10 for branch in range(12)]
            self.assertEqual(12, len(hour_stems))
            self.assertEqual(
                reference["zi_hour_start_stem_by_day_stem"][STEMS[day_stem]],
                STEMS[hour_stems[0]],
            )

    def test_independent_day_epoch_checkpoints_do_not_call_production_jdn(self):
        asset = day_epoch_asset()
        anchor = date.fromisoformat(asset["anchor_date"])
        for checkpoint in asset["independent_checkpoints"]:
            value = date.fromisoformat(checkpoint["date"])
            independent_index = (
                asset["anchor_cycle_index"] + value.toordinal() - anchor.toordinal()
            ) % 60
            self.assertEqual(checkpoint["cycle_index"], independent_index)
            self.assertEqual(checkpoint["ganzhi"], _pillar(independent_index)["ganzhi"])
            self.assertEqual(independent_index, _day_index(value)[0])

    def test_all_twelve_jie_exact_boundary_is_start_inclusive(self):
        items = {item[1]: item for item in _jie_for_year(2024)}
        self.assertEqual({entry[0] for entry in JIE}, set(items))
        for longitude, item in items.items():
            before = item[0] - timedelta(seconds=1)
            exact = item[0]
            after = item[0] + timedelta(seconds=1)
            # The engine's astronomical bracketing is directly checked at the
            # exact instant; civil-input integration is covered by the 74 assets.
            from sanji_engine.bazi.four_pillars import _surrounding_jie
            self.assertNotEqual(_surrounding_jie(before)[0][1], longitude)
            self.assertEqual(longitude, _surrounding_jie(exact)[0][1])
            self.assertEqual(longitude, _surrounding_jie(after)[0][1])

    def test_all_double_hours_and_special_zi_boundaries(self):
        expected = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        observed = []
        for hour in range(0, 24, 2):
            item = domain(request_for(record=birth_record(
                "2024-01-01", f"{hour:02d}:00:00"
            )))["four_pillars"]["hour"]
            observed.append(item["branch"])
        # Even-hour representatives start with early Zi, then Chou ... Hai, late Zi.
        self.assertEqual(expected, observed)
        for value, branch in {
            "22:59:00": "亥", "23:00:00": "子", "23:59:00": "子",
            "00:00:00": "子", "00:59:00": "子", "01:00:00": "丑",
        }.items():
            self.assertEqual(
                branch,
                domain(request_for(record=birth_record("2024-01-01", value)))[
                    "four_pillars"
                ]["hour"]["branch"],
            )

    def test_unknown_time_is_bounded_stable_and_never_fabricates_one_hour(self):
        request = request_for(record=birth_record(local_time=None))
        first = domain(request)
        second = domain(request)
        self.assertEqual(13, first["candidate_count"])
        self.assertEqual(13, first["raw_candidate_count"])
        self.assertEqual(26, first["candidate_limit"])
        self.assertIsNone(first["four_pillars"])
        self.assertEqual(["birth_time"], first["missing_data"])
        self.assertFalse(first["candidate_truncated"])
        self.assertEqual(first["candidates"], second["candidates"])
        self.assertEqual(
            sorted(item["candidate_id"] for item in first["candidates"]),
            [item["candidate_id"] for item in first["candidates"]],
        )
        dual = domain(request_for(PROFILES[2], birth_record(local_time=None)))
        self.assertEqual(26, dual["raw_candidate_count"])
        self.assertLessEqual(dual["candidate_count"], 26)
        self.assertEqual(
            dual["raw_candidate_count"] - dual["candidate_count"],
            dual["deduplication"]["merged_count"],
        )
        imprecise = birth_record(local_time="09:00:00", time_precision="double_hour")
        imprecise_result = domain(request_for(record=imprecise))
        self.assertEqual(13, imprecise_result["candidate_count"])
        self.assertEqual(["birth_time_exact"], imprecise_result["missing_data"])

    def test_all_74_boundary_assets_enter_real_engine_validation(self):
        asset = load_boundary_cases()
        outcomes = []
        for case in asset["cases"]:
            record = deepcopy(case["input"])
            for field in ("scenario", "synthetic", "offset_seconds",
                          "reference_instant_utc", "test_instant_utc"):
                record.pop(field, None)
            if "local_time" not in record:
                record["local_time"] = None
            for profile in case["profile_ids"]:
                try:
                    result = execute(request_for(profile, record, case["case_id"]))
                    outcomes.append((case["case_id"], profile, "executed", result["output_hash"]))
                except EngineError as exc:
                    # Invalid DST gaps/folds and dates outside the explicit
                    # 1900-2099 research window must fail structurally.
                    self.assertEqual("INPUT_INVALID", exc.code)
                    outcomes.append((case["case_id"], profile, "structured_rejection", exc.code))
        self.assertEqual(74, len({item[0] for item in outcomes}))
        self.assertTrue(any(item[2] == "executed" for item in outcomes))
        self.assertTrue(any(item[2] == "structured_rejection" for item in outcomes))

    def test_trace_replay_schema_and_tamper_detection(self):
        request = request_for()
        result = execute(request)
        self.assertEqual(6, len(result["trace"]))
        self.assertEqual(
            [
                "normalize_historical_civil_time", "select_profile_time_basis",
                "derive_year_pillar", "derive_month_pillar",
                "derive_day_pillar", "derive_hour_pillar",
            ],
            [step["operation"] for step in result["trace"]],
        )
        self.assertEqual(result["output_hash"], replay(result["replay_manifest"], request)["output_hash"])
        changed = deepcopy(request)
        changed["input_snapshot"]["birth_record"]["local_time"] = "12:00:01"
        with self.assertRaises(EngineError) as raised:
            replay(result["replay_manifest"], changed)
        self.assertEqual("REPLAY_INPUT_MISMATCH", raised.exception.code)
        schema = json.loads((
            ROOT / "packages/shared-types/schemas/bazi-four-pillars-engine-result.schema.json"
        ).read_text("utf-8"))
        Draft202012Validator(schema).validate(result["module_results"]["bazi"]["result"])

    def test_illegal_inputs_and_version_drift_fail_structurally(self):
        invalid_records = [
            birth_record(calendar_type="lunar"),
            birth_record(local_date="1899-12-31"),
            birth_record(timezone_id="Not/A_Zone"),
            birth_record(place={
                "latitude": "91", "longitude": "0",
                "name": "Synthetic", "precision": "fixture",
            }),
            birth_record(place={
                "latitude": 31, "longitude": "121.4",
                "name": "Synthetic", "precision": "fixture",
            }),
        ]
        for record in invalid_records:
            with self.subTest(record=record), self.assertRaises(EngineError) as raised:
                execute(request_for(record=record))
            self.assertEqual("INPUT_INVALID", raised.exception.code)
        drift = request_for()
        drift["data_versions"]["bazi_day_epoch"] = "missing"
        with self.assertRaises(EngineError) as raised:
            execute(drift)
        self.assertEqual("REPLAY_DATA_VERSION_MISMATCH", raised.exception.code)
        mixed = request_for()
        mixed["requested_modules"] = ["bazi", "calendar"]
        with self.assertRaises(EngineError) as raised:
            execute(mixed)
        self.assertEqual("INPUT_INVALID", raised.exception.code)

    def test_ruleset_and_static_scope_gates(self):
        bundle = inspect_ruleset("bazi-four-pillars-research-1.0.0")
        self.assertEqual("research_active", bundle["status"])
        self.assertFalse(bundle["production_activatable"])
        self.assertTrue(bundle["modules"]["bazi"]["enabled"])
        self.assertFalse(bundle["modules"]["bazi"]["interpretation_enabled"])
        for module in ("ziwei", "yijing", "signals", "inference", "past-life",
                       "bardo", "relationship", "life-chart"):
            self.assertFalse(bundle["modules"][module]["enabled"])
        public_surface = __import__("sanji_engine").__all__
        self.assertEqual(
            ["validate_request", "execute", "replay", "inspect_ruleset"],
            public_surface,
        )
        application_files = [
            ROOT / "apps/api/app/bazi_research_routes.py",
            ROOT / "apps/web/components/BaziResearchPreview.tsx",
        ]
        forbidden = [
            "STEMS =", "BRANCHES =", "year_stem_group", "day_stem_group",
            "calculate_year_pillar", "calculate_day_pillar",
        ]
        for path in application_files:
            text = path.read_text("utf-8")
            for marker in forbidden:
                self.assertNotIn(marker, text)

    def test_cross_platform_fixture(self):
        fixture = json.loads((
            ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/bazi/"
            "four-pillars-cross-platform-1.json"
        ).read_text("utf-8"))
        request = request_for(
            fixture["profile_id"],
            birth_record(**fixture["birth_record_overrides"]),
            "cross-platform-fixture",
        )
        result = execute(request)
        self.assertEqual(fixture["expected"]["output_hash"], result["output_hash"])
        self.assertEqual(fixture["expected"]["trace_hash"], result["trace_hash"])
        self.assertEqual(
            fixture["expected"]["domain_hash"],
            result["replay_manifest"]["domain_result_hashes"]["bazi_domain_hash"],
        )
        self.assertEqual(
            fixture["expected"]["pillars"],
            result["module_results"]["bazi"]["result"]["four_pillars"],
        )


if __name__ == "__main__":
    unittest.main()
