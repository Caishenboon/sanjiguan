"""Static release gate for Sprint 1B-1 evidence collection."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    "infra/migrations/0007_sprint1b1_evidence_foundation.sql",
    "apps/api/app/evidence_routes.py",
    "packages/evidence/reliability.py",
    "packages/evidence/completeness.py",
    "packages/evidence/three_coin.py",
    "packages/shared-types/schemas/evidence-item.schema.json",
    "packages/shared-types/schemas/three-coin-divination.schema.json",
    "apps/web/app/about/page.tsx",
    "apps/web/app/profile/[id]/onboarding/page.tsx",
]
missing = [path for path in required if not (ROOT / path).exists()]
if missing:
    raise SystemExit(f"missing Sprint 1B-1 artifacts: {missing}")

schema = json.loads((ROOT / "packages/shared-types/schemas/evidence-item.schema.json").read_text("utf-8"))
if "independent_corroboration" not in schema["properties"]:
    raise SystemExit("evidence schema field spelling drift")
if "sensation" not in schema["properties"]["domain"]["enum"]:
    raise SystemExit("sensation evidence domain missing")

route_text = (ROOT / "apps/api/app/evidence_routes.py").read_text("utf-8")
for forbidden in ("DEEPSEEK_API_KEY", "embedding", "past_life_score", "bardo_score"):
    if forbidden in route_text:
        raise SystemExit(f"forbidden Sprint 1B-1 capability: {forbidden}")
for marker in ("interpretation\": None", "record_reliability_only_not_past_life_evidence"):
    if marker not in route_text:
        raise SystemExit(f"missing non-interpretation boundary: {marker}")
print("Sprint 1B-1 static gate passed")
