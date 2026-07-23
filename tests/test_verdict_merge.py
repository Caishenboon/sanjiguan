import copy
import json
import unittest
from pathlib import Path

from packages.shared_types.verdict_merge import merge_llm_prose

ROOT = Path(__file__).resolve().parents[1]


class VerdictMergeTests(unittest.TestCase):
    def setUp(self):
        self.base = json.loads((ROOT / "tests/fixtures/demo-verdict.json").read_text(encoding="utf-8"))

    def test_only_prose_allowlist_is_merged(self):
        merged = merge_llm_prose(self.base, {"image_text": "新象辞", "judgement": {"risk": "新风险"}})
        self.assertEqual("新象辞", merged["image_text"])
        self.assertEqual("新风险", merged["judgement"]["risk"])
        self.assertEqual(self.base["strength"], merged["strength"])

    def test_malicious_locked_fields_are_rejected(self):
        attacks = [
            {"verdict": "篡改"}, {"strength": 100}, {"rank": 9},
            {"manifestation_period": {"precision": "exact"}},
            {"judgement": {"dominant_side": "risk"}},
            {"rule_ids": ["invented"]}
        ]
        for attack in attacks:
            with self.subTest(attack=attack), self.assertRaises(ValueError):
                merge_llm_prose(self.base, attack)
