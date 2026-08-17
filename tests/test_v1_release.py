from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from apps.api.app.core.runtime import load_runtime_config, session_cookie_name


class RuntimeConfigTests(unittest.TestCase):
    def test_product_inputs_never_fabricate_birth_coordinates_or_coin_tosses(self):
        root = Path(__file__).resolve().parents[1]
        subject = (root / "apps/web/components/SubjectSetup.tsx").read_text(encoding="utf-8")
        coins = (root / "apps/web/components/ThreeCoinJourney.tsx").read_text(encoding="utf-8")
        self.assertNotIn('latitude: 0, longitude: 0', subject)
        self.assertIn('coordinate_source: "user_confirmed"', subject)
        self.assertIn('useState<FaceSelection[][]>(Array.from({length:6},()=>["","",""]))', coins)
        self.assertIn('<option value="">请选择</option>', coins)

    def test_profile_patch_preserves_display_name_and_complete_birth_record(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "apps/api/app/postgres_app.py").read_text(encoding="utf-8")
        migration = (root / "infra/migrations/0022_v1_rc_original_birth_record.sql").read_text(encoding="utf-8")
        self.assertIn('if "display_name" in data:', source)
        self.assertIn('if "birth" in data:', source)
        self.assertIn("original_birth_record_ciphertext", source)
        self.assertIn("ADD COLUMN IF NOT EXISTS original_birth_record_ciphertext", migration)

    def test_member_traditional_run_policy_keeps_identity_isolation(self):
        root = Path(__file__).resolve().parents[1]
        sql = (root / "infra/migrations/0023_v1_rc_traditional_member_rls.sql").read_text(encoding="utf-8")
        self.assertIn("owner_id = app_current_user_id()", sql)
        self.assertIn("app_current_user_role() IN ('owner', 'member')", sql)
        self.assertNotIn("viewer", sql)

    def test_restore_requires_hashes_only_for_derived_archive_entries(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts/restore.py").read_text(encoding="utf-8")
        self.assertIn("entry_type <> 'record'", source)
        self.assertIn("entry_type = 'record' AND output_hash IS NULL", source)

    def test_invitation_ui_and_hash_only_issuance_are_present(self):
        root = Path(__file__).resolve().parents[1]
        start = (root / "apps/web/components/OwnerBootstrap.tsx").read_text(encoding="utf-8")
        settings = (root / "apps/web/components/MeSettings.tsx").read_text(encoding="utf-8")
        migration = (root / "infra/migrations/0024_v1_rc_invitation_issuance.sql").read_text(encoding="utf-8")
        self.assertIn("使用邀请进入", start)
        self.assertIn("/api/v1/auth/invitations/accept", start)
        self.assertIn("签发一次性邀请", settings)
        self.assertIn("p_token_hash", migration)
        self.assertNotIn("p_token text", migration)

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
