"""Dependency-free static gate for Sprint 0."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    "docs/adr/README.md",
    "docs/decision-register.md",
    "docs/plans/implementation-plan.md",
    "docs/security/threat-model.md",
    "infra/migrations/0001_sprint0_baseline.sql",
    "packages/rules/schemas/rule.schema.json",
    "packages/rules/schemas/signal.schema.json",
    "packages/rules/schemas/analysis-result.schema.json",
    "docs/api/openapi.yaml",
    "tests/golden/sprint0-inputs.json",
]
missing = [item for item in required if not (ROOT / item).exists()]
if missing:
    print("Missing:", *missing, sep="\n- ")
    sys.exit(1)

manifest = json.loads((ROOT / "packages/rules/v1.0.0/manifest.json").read_text(encoding="utf-8"))
unsafe = [
    name for name, cfg in manifest["methods"].items()
    if cfg["enabled"] or not cfg["method_id"].endswith(".UNCONFIRMED")
]
if manifest["status"] != "draft" or manifest["production_activatable"] or unsafe:
    print("Ruleset activation gate failed:", unsafe)
    sys.exit(1)

golden = json.loads((ROOT / "tests/golden/sprint0-inputs.json").read_text(encoding="utf-8"))
if len(golden["cases"]) != 10 or len({case["id"] for case in golden["cases"]}) != 10:
    print("Golden fixture count or IDs invalid")
    sys.exit(1)

print("Sprint 0 static gate passed; traditional engines remain disabled.")
