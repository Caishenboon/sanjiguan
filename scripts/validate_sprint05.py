"""Dependency-free Sprint 0.5 decision-package gate."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    "docs/decisions/method-selection-dossier.md",
    "docs/decisions/source-register.md",
    "docs/decisions/product-owner-confirmation.md",
    "docs/decisions/spec-revision-proposal.md",
    "docs/decisions/sprint1-scope.md",
]
missing = [item for item in required if not (ROOT / item).exists()]
if missing:
    print("Missing Sprint 0.5 artifacts:", *missing, sep="\n- ")
    sys.exit(1)

dossier = (ROOT / required[0]).read_text(encoding="utf-8")
register = (ROOT / "docs/decision-register.md").read_text(encoding="utf-8")
for number in range(1, 16):
    decision = f"D-{number:03d}"
    if decision not in dossier and number <= 7:
        print(f"Missing dossier section for {decision}")
        sys.exit(1)
    if decision not in register:
        print(f"Missing status register entry for {decision}")
        sys.exit(1)

for label in ("[传统原义]", "[工程事实]", "[本系统解释]", "[工程假设]"):
    if label not in dossier:
        print(f"Missing evidence-layer label: {label}")
        sys.exit(1)

manifest = json.loads((ROOT / "packages/rules/v1.0.0/manifest.json").read_text(encoding="utf-8"))
if manifest["status"] != "draft" or manifest["production_activatable"]:
    print("Ruleset must remain draft and non-activatable")
    sys.exit(1)
for method in manifest["methods"].values():
    if method["enabled"] or not method["method_id"].endswith(".UNCONFIRMED"):
        print("Traditional method activation gate failed")
        sys.exit(1)

migration = (ROOT / "infra/migrations/0001_sprint0_baseline.sql").read_text(encoding="utf-8")
if re.search(r"\bembedding\s+vector\(1024\)", migration, flags=re.IGNORECASE):
    print("Unconfirmed 1024-dimensional embedding remains hard-coded")
    sys.exit(1)
if "embedding_model_id" not in migration or "embedding_dimensions" not in migration:
    print("Embedding provenance fields are missing")
    sys.exit(1)

print("Sprint 0.5 gate passed; all production methods remain disabled.")
