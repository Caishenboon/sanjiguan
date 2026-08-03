import unittest

from scripts.validate_traditional_method_audit import validate


class TraditionalMethodAuditTests(unittest.TestCase):
    def test_registry_is_complete_and_consistent(self) -> None:
        self.assertEqual([], validate())


if __name__ == "__main__":
    unittest.main()
