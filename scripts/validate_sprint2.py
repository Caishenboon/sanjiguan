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
workflow=(ROOT/".github/workflows/deepseek-research-smoke.yml")
if workflow.exists():
    text=workflow.read_text("utf-8")
    if "workflow_dispatch:" not in text or any(trigger in text for trigger in
      ("\n  push:","\n  pull_request:","\n  schedule:","\n  workflow_run:")):
        raise SystemExit("DeepSeek smoke must be manual-only")
    if "permissions:\n  contents: read" not in text:
        raise SystemExit("DeepSeek smoke permissions are not minimal")
    if text.count("secrets.DEEPSEEK_API_KEY")!=1:
        raise SystemExit("DeepSeek secret reference must appear exactly once")
    if "retention-days: 7" not in text:
        raise SystemExit("DeepSeek artifact retention gate failed")

print("Sprint 2 gate passed: owner-only research preview; production rules remain disabled.")
