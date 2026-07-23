import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
required=[
 "docs/technical-debt/prose-quality.md","docs/pwa/install-and-cache-policy.md",
 "infra/migrations/0010_sprint3_private_research_experience.sql",
 "packages/shared-types/schemas/research-preview-launch.schema.json",
 "apps/web/public/manifest.webmanifest","apps/web/public/icon-192.svg",
 "apps/web/public/icon-512.svg","apps/web/public/sw.js",
 "apps/web/components/AppShell.tsx","apps/web/components/ResearchLaunch.tsx",
 "apps/web/components/ServiceWorkerRegistration.tsx",
]
missing=[path for path in required if not (ROOT/path).exists()]
if missing:raise SystemExit(f"missing Sprint 3 artifacts: {missing}")
workflow=(ROOT/".github/workflows/ci.yml").read_text("utf-8")
if "DEEPSEEK_API_KEY" in workflow:raise SystemExit("ordinary CI must not consume DeepSeek secret")
sw=(ROOT/"apps/web/public/sw.js").read_text("utf-8")
for sensitive in ('"/api/"','"/profile/"'):
    if sensitive not in sw:raise SystemExit(f"sensitive cache exclusion missing: {sensitive}")
manifest=json.loads((ROOT/"packages/rules/v1.0.0/manifest.json").read_text("utf-8"))
if manifest["status"]!="draft" or manifest["production_activatable"]:
    raise SystemExit("production rules activated")
print("Sprint 3 gate passed: private owner research only; production rules remain disabled.")
