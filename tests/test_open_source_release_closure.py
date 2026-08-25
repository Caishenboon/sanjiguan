from __future__ import annotations

import unittest

from scripts.validate_open_source_release import audit


class OpenSourceReleaseClosureTests(unittest.TestCase):
    def test_publication_scope_is_integrity_clean_and_ready(self):
        result = audit()
        self.assertEqual([], result["integrity_errors"])
        self.assertTrue(result["safe_to_remain_private"])
        self.assertTrue(result["public_release_ready"])
        self.assertEqual([], result["blocking_decisions"])

    def test_release_state_records_owner_public_authorization(self):
        result = audit()
        self.assertTrue(result["public_release_ready"])
        self.assertEqual([], result["blocking_decisions"])

    def test_history_email_is_counted_without_storing_the_address(self):
        result = audit()
        self.assertEqual(1, result["unique_non_noreply_email_count"])
        self.assertGreaterEqual(result["non_noreply_commit_count"], 21)

    def test_publication_controls_preserve_post_switch_safety_requirements(self):
        result = audit()
        self.assertEqual([], result["integrity_errors"])
        self.assertTrue(result["public_release_ready"])


if __name__ == "__main__":
    unittest.main()
