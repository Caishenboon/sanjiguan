import hashlib
import json
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def canonical_hash(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Sprint0BaselineTests(unittest.TestCase):
    def test_ten_golden_inputs_exist_and_hash_deterministically(self):
        fixture = json.loads((ROOT / "tests/golden/sprint0-inputs.json").read_text(encoding="utf-8"))
        self.assertEqual(10, len(fixture["cases"]))
        first = fixture["cases"][0]
        self.assertEqual(canonical_hash(first), canonical_hash(json.loads(json.dumps(first, ensure_ascii=False))))
        self.assertRegex(canonical_hash(first), r"^[a-f0-9]{64}$")

    def test_traditional_engines_are_not_activated(self):
        manifest = json.loads((ROOT / "packages/rules/v1.0.0/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("draft", manifest["status"])
        self.assertFalse(manifest["production_activatable"])
        for config in manifest["methods"].values():
            self.assertFalse(config["enabled"])
            self.assertTrue(config["method_id"].endswith(".UNCONFIRMED"))

    def test_example_environment_has_no_secret(self):
        text = (ROOT / ".env.example").read_text(encoding="utf-8")
        line = next(line for line in text.splitlines() if line.startswith("DEEPSEEK_API_KEY="))
        self.assertEqual("DEEPSEEK_API_KEY=", line)
        self.assertNotIn("NEXT_PUBLIC_DEEPSEEK", text)

    def test_gitignore_protects_env_files(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".env.*", text)
        self.assertIn("!.env.example", text)

    def test_rule_schemas_parse_as_json(self):
        for path in (ROOT / "packages/rules/schemas").glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))

    def test_api_contract_requires_backend_session(self):
        text = (ROOT / "docs/api/openapi.yaml").read_text(encoding="utf-8")
        self.assertIn("sessionCookie", text)
        self.assertIn("Idempotency-Key", text)
        self.assertNotIn("DEEPSEEK_API_KEY", text)

    def test_migration_enables_rls_and_encryption_fields(self):
        text = (ROOT / "infra/migrations/0001_sprint0_baseline.sql").read_text(encoding="utf-8")
        self.assertIn("ENABLE ROW LEVEL SECURITY", text)
        self.assertIn("input_snapshot_encrypted bytea", text)
        self.assertIn("payload_encrypted bytea", text)

    def test_no_obvious_deepseek_secret_pattern_in_tracked_sources(self):
        suspicious = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
        excluded = {".git", "work", "outputs"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or any(part in excluded for part in path.parts):
                continue
            if path.suffix.lower() in {".docx", ".png", ".pdf", ".pyc"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            self.assertIsNone(suspicious.search(text), str(path))


if __name__ == "__main__":
    unittest.main()
