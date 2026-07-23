"""Sprint 1A.5 fail-closed artifact and forbidden-scope gate."""

import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    "infra/migrations/0003_sprint1a5_authorization.sql",
    "apps/api/app/services/postgres.py",
    "apps/api/app/services/repository.py",
    "packages/shared-types/schemas/verdict.schema.json",
    "tests/test_postgres_integration.py",
    "docs/product/terminology.yml",
    "docs/product/voice-and-terminology.md",
    "docs/security/rls-permission-matrix.md",
]
missing = [name for name in required if not (root / name).is_file()]
if missing:
    raise SystemExit(f"missing Sprint 1A.5 artifacts: {missing}")

manifest = json.loads((root / "packages/rules/v1.0.0/manifest.json").read_text(encoding="utf-8"))
assert manifest["status"] == "draft" and not manifest["production_activatable"]
assert all(not method["enabled"] and method["method_id"].endswith(".UNCONFIRMED")
           for method in manifest["methods"].values())

ci = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
for marker in ("image: postgres:16", "scripts/migrate.py", "test_postgres_integration"):
    if marker not in ci:
        raise SystemExit(f"real PostgreSQL CI marker missing: {marker}")

for script in ("scripts/check_product_language.py", "scripts/check_secrets.py"):
    result = subprocess.run([sys.executable, script], cwd=root, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
print("Sprint 1A.5 gate passed; production divination rules remain disabled.")
