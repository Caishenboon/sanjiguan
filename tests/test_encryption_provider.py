import unittest

from apps.api.app.core.encryption import TestKeyProvider, assert_key_provider_allowed


class EncryptionProviderTests(unittest.TestCase):
    def test_test_provider_round_trip_and_production_gate(self):
        provider = TestKeyProvider(b"x" * 32)
        encrypted = provider.encrypt(b"sensitive", b"profile")
        self.assertNotIn(b"sensitive", encrypted)
        self.assertEqual(b"sensitive", provider.decrypt(encrypted, b"profile"))
        with self.assertRaisesRegex(RuntimeError, "test_key_provider_forbidden_in_production"):
            assert_key_provider_allowed("production", provider)
