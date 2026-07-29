"""Static release gates for the Sprint 17 research-only topic engines."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


rules = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/rulesets/assets/topic-research-rules-1.0.0.json").read_text(encoding="utf-8"))
names = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/rulesets/assets/past-life-name-rules-1.0.0.json").read_text(encoding="utf-8"))
bundle = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/rulesets/topic-research-v1.0.0.json").read_text(encoding="utf-8"))
cases = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/topics/topic-conformance-v1.json").read_text(encoding="utf-8"))
migration = (ROOT / "infra/migrations/0017_topic_engines_v1.sql").read_text(encoding="utf-8")
engine = (ROOT / "packages/sanji-engine/src/sanji_engine/topics/v1.py").read_text(encoding="utf-8")
api = (ROOT / "apps/api/app/topic_routes.py").read_text(encoding="utf-8")
web = "\n".join(
    (ROOT / path).read_text(encoding="utf-8")
    for path in (
        "apps/web/components/TopicResearch.tsx",
        "apps/web/lib/product-language.ts",
    )
)

for asset in (rules, names):
    require(asset["tradition_scope"] == "sanji_original", "topic assets must be Sanji-original")
    require(asset["activation"] == "research_active", "topic assets must stay research_active")
    require(asset["review_status"] == "UNCONFIRMED", "topic assets must stay UNCONFIRMED")
    require(asset["production_activatable"] is False, "production activation is forbidden")
require(bundle["production_activatable"] is False, "bundle cannot be production activatable")
for topic in ("sushe", "zhongyin_life", "zhongyin_deceased", "yuanqi"):
    capability = bundle["topic_capabilities"][topic]
    require(capability["enabled"] is True, f"topic capability missing: {topic}")
    require(capability["status"] == "research_active", f"topic must stay research_active: {topic}")
    require(capability["review_status"] == "UNCONFIRMED", f"topic must stay UNCONFIRMED: {topic}")
    require(capability["production_activatable"] is False, f"topic production activation forbidden: {topic}")
for module in ("bazi", "ziwei", "yijing", "past-life", "bardo", "relationship", "life-chart"):
    require(bundle["modules"][module]["enabled"] is False, f"{module} must not become an executable public module")
require(cases["case_count"] == 72 and len(cases["cases"]) == 72, "72 synthetic cases required")
require(cases["asset_class"] == "synthetic_conformance", "cases may not claim real validation")
require(sum("topic-sushe" in item["case_id"] for item in cases["cases"]) == 24, "24 Sushe cases required")
require(sum("zhongyin" in item["case_id"] for item in cases["cases"]) == 24, "24 Zhongyin cases required")
require(sum("yuanqi" in item["case_id"] for item in cases["cases"]) == 24, "24 Yuanqi cases required")
for table in ("topic_executions", "topic_execution_evidence_refs", "topic_replay_records", "topic_execution_comparisons"):
    require(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in migration, f"FORCE RLS missing: {table}")
require("owner_id = app_current_user_id()" in migration, "resource-owner RLS missing")
require("execute(request)" in api and "replay(row[\"replay_manifest\"]" in api, "API must call public engine")
require("dream_text" in engine and "private narrative is forbidden" in engine, "sensitive prose gate missing")
for forbidden in ("requests.", "httpx.", "openai", "deepseek_api", "oracle_adapter"):
    require(forbidden not in engine.lower(), f"engine external dependency forbidden: {forbidden}")
require("generated_identity" in web and "epistemicDisplay" in web, "visible epistemic name labels required")
require("命定伴侣" not in engine and "必然复合" not in engine, "absolute relationship claims forbidden")
print("Sprint 17 topic-engine static gates passed")
