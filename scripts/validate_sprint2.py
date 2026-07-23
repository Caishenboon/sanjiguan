import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from packages.research_inference.engine import run_inference
required=["infra/migrations/0009_sprint2_research_inference.sql","apps/api/app/research_routes.py",
"packages/research_inference/engine.py","packages/research_inference/providers.py",
"knowledge/research/scoring-config.json","tests/fixtures/sprint2-evaluation-cases.json",
"prompts/research-preview-pass1.md","prompts/research-preview-pass2.md",
"packages/shared-types/schemas/normalized-signal.schema.json",
"packages/shared-types/schemas/research-verdict.schema.json",
"apps/web/app/admin/research/analyses/page.tsx"]
missing=[p for p in required if not (ROOT/p).exists()]
if missing:raise SystemExit(f"missing Sprint 2 artifacts: {missing}")
cases=json.loads((ROOT/"tests/fixtures/sprint2-evaluation-cases.json").read_text("utf-8"))
if len(cases)<30 or any("real_user" in json.dumps(c) for c in cases):raise SystemExit("fixture gate failed")
config=json.loads((ROOT/"knowledge/research/scoring-config.json").read_text("utf-8"))
if "not probability" not in config.get("notice",""):
    raise SystemExit("research strength must explicitly disclaim probability")
repo=(ROOT/"apps/api/app/research_routes.py").read_text("utf-8")
if "run_mode='production'" in repo or "production_activatable=true" in repo.lower():
    raise SystemExit("production inference activation detected")
provider=(ROOT/"packages/research_inference/providers.py").read_text("utf-8")
if "NEXT_PUBLIC_" in provider:raise SystemExit("frontend-visible provider secret detected")
for phrase in ("佛菩萨转世","高僧转世","前世概率"):
    if phrase in repo:raise SystemExit(f"forbidden output phrase: {phrase}")
print("Sprint 2 gate passed: owner-only research preview; production rules remain disabled.")
