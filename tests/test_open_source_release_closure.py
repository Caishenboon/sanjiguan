from __future__ import annotations

import unittest

from scripts.validate_open_source_release import audit


class OpenSourceReleaseClosureTests(unittest.TestCase):
    def test_private_closure_is_integrity_clean_and_publication_is_blocked(self):
        result = audit()
        self.assertEqual([], result["integrity_errors"])
        self.assertTrue(result["safe_to_remain_private"])
        self.assertFalse(result["public_release_ready"])
        self.assertIn("PROJECT_LICENSE_NOT_ACTIVATED", result["blocking_decisions"])
        self.assertIn(
            "NON_NOREPLY_COMMIT_HISTORY_DECISION_REQUIRED", result["blocking_decisions"]
        )
        self.assertIn("DEMO_FIXTURE_HUMAN_REVIEW_REQUIRED", result["blocking_decisions"])

    def test_release_state_never_claims_public_authorization(self):
        result = audit()
        self.assertFalse(result["public_release_ready"])
        self.assertGreaterEqual(len(result["blocking_decisions"]), 9)

    def test_history_email_is_counted_without_storing_the_address(self):
        result = audit()
        self.assertEqual(20, result["non_noreply_commit_count"])

    def test_publication_controls_are_prepared_without_authorizing_publication(self):
        result = audit()
        self.assertEqual([], result["integrity_errors"])
        self.assertFalse(result["public_release_ready"])
        self.assertIn(
            "OWNER_FINAL_PUBLIC_SWITCH_CONFIRMATION_REQUIRED",
            result["blocking_decisions"],
        )


if __name__ == "__main__":
    unittest.main()
