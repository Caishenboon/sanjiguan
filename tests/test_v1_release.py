from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from apps.api.app.core.runtime import load_runtime_config, session_cookie_name


class RuntimeConfigTests(unittest.TestCase):
    def test_web_proxy_preserves_runtime_issued_session_cookie_name(self):
        route = (
            Path(__file__).resolve().parents[1]
            / "apps"
            / "web"
            / "app"
            / "api"
            / "[...path]"
            / "route.ts"
        ).read_text(encoding="utf-8")
        self.assertNotIn('cookie.replace(', route)
        self.assertIn('"cookie"', route)

    def test_session_cookie_name_is_shared_by_development_and_production_routes(self):
        self.assertEqual(session_cookie_name("development"), "sanji-session")
        self.assertEqual(session_cookie_name("production"), "__Host-session")

    def test_production_rejects_http_and_weak_or_missing_secret(self):
        env = {
            "APP_ENV": "production",
            "DATABASE_URL": "dbname=sanjiguan user=app_runtime password=opaque host=postgres",
            "PUBLIC_ORIGIN": "http://example.invalid",
            "KEY_PROVIDER": "env-aesgcm",
            "FIELD_ENCRYPTION_KEY_HEX": "11" * 32,
            "FIELD_ENCRYPTION_KEY_ID": "v1",
            "SESSION_COOKIE_SECURE": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(RuntimeError, "https"):
                load_runtime_config()

    def test_production_accepts_explicit_safe_configuration(self):
        env = {
            "APP_ENV": "production",
            "DATABASE_URL": "dbname=sanjiguan user=app_runtime password=opaque host=postgres",
            "PUBLIC_ORIGIN": "https://sanji.invalid",
            "KEY_PROVIDER": "env-aesgcm",
            "FIELD_ENCRYPTION_KEY_HEX": "22" * 32,
            "FIELD_ENCRYPTION_KEY_ID": "field-key-v1",
            "SESSION_COOKIE_SECURE": "true",
            "OWNER_BOOTSTRAP_TOKEN": "x" * 40,
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_runtime_config()
        self.assertTrue(config.production)
        self.assertTrue(config.cookie_secure)

    def test_development_can_use_local_http_but_is_explicit(self):
        env = {
            "APP_ENV": "development",
            "DATABASE_URL": "dbname=sanjiguan user=app_runtime password=opaque host=postgres",
            "KEY_PROVIDER": "env-aesgcm",
            "FIELD_ENCRYPTION_KEY_HEX": "33" * 32,
            "FIELD_ENCRYPTION_KEY_ID": "local-v1",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_runtime_config()
        self.assertFalse(config.production)
        self.assertFalse(config.cookie_secure)


if __name__ == "__main__":
    unittest.main()
