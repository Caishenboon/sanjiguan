from __future__ import annotations

import json
import unittest
from pathlib import Path

from sanji_engine import execute
from sanji_engine.canonical import content_hash
from sanji_engine.errors import EngineError
from tests.test_sanji_engine_bazi_four_pillars import birth_record, request_for

ROOT = Path(__file__).resolve().parents[1]
GOLDENS = ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/bazi/mechanical-trust-goldens-1.0.0.json"


class MechanicalTrustCrossPlatformTests(unittest.TestCase):
    def test_new_golden_aggregate_and_all_engine_outcomes(self):
        asset = json.loads(GOLDENS.read_text("utf-8"))
        self.assertEqual(
            "sha256:20cba2932d0d800590aa26fd0dd954f5c621d194c909f0a638844dced836b139",
            content_hash(asset["cases"]),
        )
        outcomes = []
        for case in asset["cases"]:
            value = case["input"]
            record = birth_record(
                value["local_date"], value["local_time"], timezone_id=value["timezone_id"]
            )
            record["place"]["longitude"] = value["longitude"]
            try:
                result = execute(request_for(case["profile_id"], record, case["case_id"]))
            except EngineError as exc:
                self.assertEqual(case["expected"].get("error_code"), exc.code)
                outcomes.append((case["case_id"], "error", exc.code))
                continue
            domain = result["module_results"]["bazi"]["result"]
            expected = case["expected"]
            if "pillars" in expected:
                actual = {
                    key: item["ganzhi"]
                    for key, item in domain["candidates"][0]["pillars"].items()
                }
                self.assertEqual(expected["pillars"], actual)
            outcomes.append((case["case_id"], "success", result["output_hash"], result["trace_hash"]))
        self.assertEqual(13, len(outcomes))
        self.assertEqual(len(outcomes), len({item[0] for item in outcomes}))


if __name__ == "__main__":
    unittest.main()
