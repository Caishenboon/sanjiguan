import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from apps.api.app.schemas.models import OriginalBirthRecord
from packages.engine.normalization.birth_time import normalize_birth_time
from packages.engine.normalization.solar_terms import solar_term_instant

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "tests/golden/sprint1a-time-fixtures.json").read_text(encoding="utf-8"))


def record(local: str, zone: str, longitude: float = 0.0) -> OriginalBirthRecord:
    value = datetime.fromisoformat(local)
    return OriginalBirthRecord.model_validate({
        "calendar_type": "gregorian",
        "local_date": value.date().isoformat(),
        "local_time": value.time().isoformat(),
        "timezone_id": zone,
        "timezone_database": "IANA",
        "timezone_database_version": "system-under-test",
        "time_precision": "minute",
        "place": {
            "label": "fixture",
            "latitude": 0,
            "longitude": longitude,
            "coordinate_source": "golden_fixture"
        },
        "user_confirmed": True,
        "captured_at": "2026-07-23T00:00:00+00:00"
    })


class Sprint1ATimeTests(unittest.TestCase):
    def test_iana_offsets_and_dst(self):
        for case in FIXTURES["timezone_cases"]:
            result = normalize_birth_time(record(case["local"], case["zone"]))
            self.assertEqual(case["expected_offset_minutes"], result.historical_utc_offset_minutes, case["id"])
            self.assertEqual(case["expected_dst_minutes"], result.dst_offset_minutes, case["id"])
            civil = next(item for item in result.candidates if item.basis == "civil")
            self.assertEqual(datetime.fromisoformat(case["expected_utc"]), civil.utc_datetime, case["id"])

    def test_invalid_or_ambiguous_local_times_are_rejected(self):
        for case in FIXTURES["invalid_local_times"]:
            with self.assertRaises(ValueError, msg=case["id"]):
                normalize_birth_time(record(case["local"], case["zone"]))

    def test_no_candidate_is_selected_as_primary_chart(self):
        result = normalize_birth_time(record("1990-01-15T08:30:00", "Asia/Shanghai", 121.4737))
        self.assertTrue(all(not item.is_primary_chart for item in result.candidates))
        self.assertIn("不得输出最终日柱或子时换日结论", result.prohibited_conclusions)

    def test_longitude_and_dst_correction_chain(self):
        result = normalize_birth_time(record("2020-07-01T12:00:00", "America/New_York", -74.006))
        self.assertAlmostEqual(3.976, result.longitude_correction_minutes, places=6)
        self.assertEqual(60, result.dst_offset_minutes)
        mean = next(item for item in result.candidates if item.basis == "local_mean_solar")
        self.assertEqual(datetime.fromisoformat("2020-07-01T11:03:58.560000"), mean.local_datetime)

    def test_unknown_time_creates_interval_not_fake_instant(self):
        value = OriginalBirthRecord.model_validate({
            "calendar_type": "gregorian",
            "local_date": "1988-06-20",
            "local_time": None,
            "timezone_id": "Asia/Shanghai",
            "timezone_database": "IANA",
            "timezone_database_version": "system-under-test",
            "time_precision": "unknown",
            "place": {"latitude": 31.2, "longitude": 121.47, "coordinate_source": "user"},
            "user_confirmed": True,
            "captured_at": "2026-07-23T00:00:00+00:00"
        })
        result = normalize_birth_time(value)
        self.assertEqual("unknown_interval", result.candidates[0].basis)
        self.assertIsNone(result.candidates[0].local_datetime)

    def test_solar_terms_match_hko_within_two_minutes(self):
        tolerance = FIXTURES["tolerances"]["solar_term_seconds"]
        for case in FIXTURES["solar_term_cases"]:
            actual = solar_term_instant(
                case["longitude"],
                datetime.fromisoformat(case["search_start_utc"]),
            )
            expected = datetime.fromisoformat(case["expected_utc"])
            self.assertLessEqual(abs((actual - expected).total_seconds()), tolerance, case["id"])


if __name__ == "__main__":
    unittest.main()
