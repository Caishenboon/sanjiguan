"""Static release gates for Sprint 16 private evidence and archive."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


policy = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/rulesets/assets/liuxiang-evidence-policies-1.0.0.json").read_text(encoding="utf-8"))
mapping = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/rulesets/assets/liuxiang-evidence-mappings-1.0.0.json").read_text(encoding="utf-8"))
bundle = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/rulesets/liuxiang-evidence-research-v1.0.0.json").read_text(encoding="utf-8"))
cases = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/liuxiang/user-evidence-conformance-v1.json").read_text(encoding="utf-8"))
migration = (ROOT / "infra/migrations/0016_liuxiang_evidence_archive_v1.sql").read_text(encoding="utf-8")
route = (ROOT / "apps/api/app/liuxiang_archive_routes.py").read_text(encoding="utf-8")
web = "\n".join(
    (ROOT / item).read_text(encoding="utf-8")
    for item in (
        "apps/web/components/LiuxiangReadiness.tsx",
        "apps/web/components/ChronicleList.tsx",
        "apps/web/components/ChronicleDetail.tsx",
    )
)

require(len(policy["policies"]) == 6, "six evidence policies required")
require({item["dimension_id"] for item in policy["policies"]} == {
    "lx_ming", "lx_ye", "lx_yuan", "lx_meng", "lx_yuan_relation", "lx_shi"
}, "evidence policy dimensions drift")
for value in (policy, mapping, bundle):
    require(value["review_status"] == "UNCONFIRMED", "review status must remain UNCONFIRMED")
    require(value["production_activatable"] is False, "production activation forbidden")
require(bundle["status"] == "research_active", "bundle must remain research_active")
for module in ("bazi", "ziwei", "yijing", "past-life", "bardo", "relationship", "life-chart"):
    require(bundle["modules"][module]["enabled"] is False, f"{module} must remain disabled")
require(all(rule["activation_status"] == "research_active" for rule in mapping["rules"]),
        "only explicit user-evidence research mappings are expected")
require(all("INTERPRET" not in rule["mapping_rule_id"] for rule in mapping["rules"]),
        "interpretive mappings must not be enabled")
require(cases["case_count"] == 72 and len(cases["cases"]) == 72, "72 synthetic cases required")
require(cases["asset_class"] == "synthetic_conformance", "cases must not claim reality validation")
require(policy["content_hash"] in migration, "migration policy manifest hash drift")
for table in (
    "liuxiang_user_executions", "liuxiang_execution_evidence_refs",
    "sanji_archive_entries", "liuxiang_replay_records",
    "liuxiang_execution_comparisons",
):
    require(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in migration, f"FORCE RLS missing: {table}")
require("owner_id = app_current_user_id()" in migration, "strict resource ownership missing")
require("execute(request)" in route and "replay(row[\"replay_manifest\"]" in route,
        "thin API must call sanji-engine execute/replay")
for forbidden in ("DeepSeek", "Oracle", "llm_score", "sessionStorage.setItem"):
    require(forbidden not in route, f"private API forbidden dependency: {forbidden}")
require("/api/v1/chronicle" in web and "sessionStorage" not in web,
        "archive UI must use database API, not browser session authority")
print("Liuxiang evidence/archive v1 static gates passed")
