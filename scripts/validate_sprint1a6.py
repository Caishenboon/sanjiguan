"""Validate Sprint 1A.6 evidence, provenance contract, and closed rule gates."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
evidence = json.loads((root / "outputs/postgres16-evidence.json").read_text(encoding="utf-8"))
summary = json.loads((root / "outputs/test-summary.json").read_text(encoding="utf-8"))
schema = json.loads((root / "packages/shared-types/schemas/verdict.schema.json").read_text(encoding="utf-8"))
manifest = json.loads((root / "packages/rules/v1.0.0/manifest.json").read_text(encoding="utf-8"))

if not evidence["postgresql_version"].startswith("16."):
    raise SystemExit("real PostgreSQL 16 evidence missing")
if evidence["postgres_integration"] != {"passed": 5, "failed": 0, "skipped": 0}:
    raise SystemExit("PostgreSQL integration evidence is not green")
if evidence["api_postgres_e2e"] != {"passed": 1, "failed": 0, "skipped": 0}:
    raise SystemExit("HTTP PostgreSQL E2E evidence is not green")
if evidence["migration_second_run_changes"] or evidence["residual_users_after_tests"]:
    raise SystemExit("migration idempotency or cleanup evidence failed")
for field in ("provenance", "locked_fields"):
    if field not in schema["properties"]:
        raise SystemExit(f"verdict provenance contract missing {field}")
if "created_by" in schema["properties"] or "engine_fields_locked" in schema["properties"]:
    raise SystemExit("deprecated verdict provenance fields remain")
if summary["total_skipped"] != 0 or any(
    value.get("failed", 0) for value in summary.values() if isinstance(value, dict)
):
    raise SystemExit("test summary contains failures or skipped-as-passed ambiguity")
if manifest["status"] != "draft" or manifest["production_activatable"]:
    raise SystemExit("production rule gate opened")
if any(method["enabled"] for method in manifest["methods"].values()):
    raise SystemExit("a traditional method is enabled")
print("Sprint 1A.6 evidence and contract gate passed.")
