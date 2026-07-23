"""Fail closed when Sprint 1A scope, schemas, or rule gates drift."""

import json
import re
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("STORAGE_BACKEND", "memory")

required = [
    "apps/api/app/main.py",
    "apps/web/package.json",
    "infra/migrations/0002_sprint1a_foundation.sql",
    "packages/shared-types/birth-record.schema.json",
    "packages/shared-types/birth-time-normalization.schema.json",
    "packages/shared-types/solar-term-instant.schema.json",
    "docs/api/openapi.generated.json",
    "tests/golden/sprint1a-time-fixtures.json",
]
missing = [name for name in required if not (ROOT / name).is_file()]
if missing:
    raise SystemExit(f"missing Sprint 1A artifacts: {missing}")

manifest = json.loads((ROOT / "packages/rules/v1.0.0/manifest.json").read_text(encoding="utf-8"))
if manifest["status"] != "draft" or manifest["production_activatable"]:
    raise SystemExit("traditional rules must remain draft and non-activatable")
for name, method in manifest["methods"].items():
    if method["enabled"] or not method["method_id"].endswith(".UNCONFIRMED"):
        raise SystemExit(f"{name} must remain disabled and UNCONFIRMED")

env = (ROOT / ".env.example").read_text(encoding="utf-8")
for flag in ("RULESET_BAZI_ENABLED=false", "RULESET_ZIWEI_ENABLED=false", "RULESET_YIJING_ENABLED=false"):
    if flag not in env:
        raise SystemExit(f"missing fail-closed setting: {flag}")
if not re.search(r"(?m)^DEEPSEEK_API_KEY=\s*$", env):
    raise SystemExit("example environment must not contain a DeepSeek key")

prohibited_paths = [
    "packages/engine/bazi",
    "packages/engine/ziwei",
    "packages/engine/yijing",
    "packages/engine/past_life",
    "packages/engine/bardo",
]
present = [
    name
    for name in prohibited_paths
    if (ROOT / name).exists()
    and any(path.is_file() for path in (ROOT / name).rglob("*"))
]
if present:
    raise SystemExit(f"prohibited Sprint 1A implementation paths exist: {present}")

generated = json.loads((ROOT / "docs/api/openapi.generated.json").read_text(encoding="utf-8"))
from apps.api.app.main import app
if generated != app.openapi():
    raise SystemExit("OpenAPI drift: run scripts/export_openapi.py")

print("Sprint 1A validation passed: rules disabled, scope gated, OpenAPI synchronized.")
