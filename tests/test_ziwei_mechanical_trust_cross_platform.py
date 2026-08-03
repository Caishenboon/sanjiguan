from __future__ import annotations

import json
import unittest
from pathlib import Path

from sanji_engine.canonical import content_hash
from tests.test_ziwei_mechanical_trust import run_case

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/ziwei/mechanical-trust-references-1.0.0.json"


class ZiweiMechanicalTrustCrossPlatformTests(unittest.TestCase):
    def test_reference_aggregate_and_engine_hashes_are_platform_stable(self):
        asset = json.loads(REFERENCES.read_text("utf-8"))
        self.assertEqual(
            "sha256:97d96f973c611e9ecf91cc45acdb99dcc15a9f0970c4275128e48170f123dbbe",
            content_hash(asset["cases"]),
        )
        outcomes = []
        for case in asset["cases"]:
            primary = run_case(case)
            outcomes.append((case["case_id"], primary["output_hash"], primary["trace_hash"]))
            if case.get("alternate_profile_id"):
                alternate = run_case(case, case["alternate_profile_id"])
                outcomes.append((case["case_id"] + ":alternate", alternate["output_hash"], alternate["trace_hash"]))
        self.assertEqual(13, len(outcomes))
        self.assertEqual(len(outcomes), len({item[0] for item in outcomes}))


if __name__ == "__main__":
    unittest.main()
