import unittest

from packages.evidence.completeness import DOMAINS, completeness_state, summarize_completeness
from packages.evidence.reliability import assess_reliability
from packages.evidence.three_coin import map_coin_faces, validate_six_tosses


class EvidenceFoundationTests(unittest.TestCase):
    def test_reliability_is_bounded_and_explicitly_non_metaphysical(self):
        result = assess_reliability({
            "source_type": "document", "frequency": 4, "first_observed_age": 8,
            "independent_corroboration": True, "specific_description": True,
            "possible_ordinary_explanations": [], "memory_reshaping_risk": False,
        })
        self.assertLessEqual(result["reliability_score"], 1)
        self.assertEqual(result["meaning"], "record_reliability_only_not_past_life_evidence")

    def test_completeness_preserves_unknown_and_explicit_none(self):
        states = {domain: "not_filled" for domain in DOMAINS}
        states["dream"] = completeness_state("unknown")
        states["sensation"] = completeness_state("explicit_none")
        result = summarize_completeness(states)
        self.assertEqual(result["dimensions"]["dream"], "unknown")
        self.assertIn("not_fortune_or_spiritual_score", result["meaning"])

    def test_physical_three_coin_values_and_order(self):
        self.assertEqual(map_coin_faces(["heads", "heads", "heads"]), [3, 3, 3])
        tosses = [{"line_no": i, "coin_faces": ["tails", "tails", "tails"],
                   "was_retossed": False} for i in range(1, 7)]
        self.assertEqual(
            [line["coin_values"] for line in validate_six_tosses(tosses)],
            [[2, 2, 2]] * 6,
        )
        with self.assertRaisesRegex(ValueError, "six_lines"):
            validate_six_tosses(list(reversed(tosses)))


if __name__ == "__main__":
    unittest.main()
