import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Sprint1ASecurityContractTests(unittest.TestCase):
    def test_rls_is_forced_and_runtime_role_cannot_bypass(self):
        sql = (ROOT / "infra/migrations/0002_sprint1a_foundation.sql").read_text(encoding="utf-8")
        self.assertIn("NOBYPASSRLS", sql)
        self.assertIn("FORCE ROW LEVEL SECURITY", sql)
        self.assertNotIn("ALTER TABLE profiles OWNER TO app_runtime", sql)
        self.assertIn("profile_grants", sql)

    def test_idempotency_contract_is_24_hours_and_scoped(self):
        sql = (ROOT / "infra/migrations/0002_sprint1a_foundation.sql").read_text(encoding="utf-8")
        for field in ["owner_id", "http_method", "route_template", "key_hash", "request_fingerprint"]:
            self.assertIn(field, sql)
        self.assertIn("interval '24 hours'", sql)

    def test_relationship_consent_fields_exist(self):
        sql = (ROOT / "infra/migrations/0002_sprint1a_foundation.sql").read_text(encoding="utf-8")
        for field in ["consent_version", "status", "consented_at", "revoked_at", "proof_type"]:
            self.assertIn(field, sql)

    def test_blocked_algorithm_terms_are_absent_from_source_modules(self):
        blocked_assignments = re.compile(
            r"(day_pillar|bazi_strength|favorable_element|past_life_score|bardo_score|celebrity_match)\\s*=",
            flags=re.IGNORECASE,
        )
        for root in [ROOT / "apps", ROOT / "packages/engine"]:
            for path in root.rglob("*"):
                if path.is_file() and path.suffix in {".py", ".ts", ".tsx", ".js"}:
                    self.assertIsNone(blocked_assignments.search(path.read_text(encoding="utf-8")), str(path))


if __name__ == "__main__":
    unittest.main()
