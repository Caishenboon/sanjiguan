import json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from packages.knowledge_governance.policy import archetype_errors
required=["infra/migrations/0008_sprint1b2_knowledge_workbench.sql",
"packages/shared-types/schemas/knowledge-document.schema.json",
"packages/shared-types/schemas/knowledge-claim.schema.json",
"packages/shared-types/schemas/rule-draft.schema.json","docs/knowledge/source-register.md",
"docs/decisions/ADR-0010-responsive-pwa.md","docs/decisions/sprint1b2-blockers.md",
"knowledge/research/archetypes.json","apps/api/app/knowledge_routes.py",
"apps/web/app/admin/knowledge/page.tsx"]
missing=[p for p in required if not (ROOT/p).exists()]
if missing: raise SystemExit(f"missing Sprint 1B-2 artifacts: {missing}")
rules=json.loads((ROOT/"packages/shared-types/schemas/rule-draft.schema.json").read_text("utf-8"))
if rules["properties"]["production_activatable"].get("const") is not False:
    raise SystemExit("production activation not statically disabled")
archetypes=json.loads((ROOT/"knowledge/research/archetypes.json").read_text("utf-8"))
errors=archetype_errors(archetypes)
if errors: raise SystemExit(f"archetype gate failed: {errors}")
repo="\n".join(p.read_text("utf-8",errors="ignore") for p in [
    ROOT/"apps/api/app/knowledge_routes.py",ROOT/"knowledge/research/archetypes.json"])
for forbidden in ("DEEPSEEK_API_KEY","embedding_model_id","past_life_score","bardo_score"):
    if forbidden in repo: raise SystemExit(f"forbidden capability in Sprint 1B-2: {forbidden}")
print("Sprint 1B-2 knowledge and rule gates passed; production rules remain disabled.")
