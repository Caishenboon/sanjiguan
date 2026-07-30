"""Static release gates for deterministic Sprint 18 research capabilities."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)

asset = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/rulesets/assets/life-trend-rules-1.0.0.json").read_text(encoding="utf-8"))
bundle = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/rulesets/life-trend-research-v1.0.0.json").read_text(encoding="utf-8"))
cases = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/life_trend/life-trend-conformance-v1.json").read_text(encoding="utf-8"))
migration = (ROOT / "infra/migrations/0018_life_trend_report_v1.sql").read_text(encoding="utf-8")
engine = (ROOT / "packages/sanji-engine/src/sanji_engine/life_chart/v1.py").read_text(encoding="utf-8")
api = (ROOT / "apps/api/app/life_trend_routes.py").read_text(encoding="utf-8")

require(asset["tradition_scope"] == "sanji_original", "life trend must be Sanji-original")
require(asset["activation"] == "research_active", "life trend must stay research_active")
require(asset["review_status"] == "UNCONFIRMED", "life trend must stay UNCONFIRMED")
require(asset["production_activatable"] is False, "production activation forbidden")
require(bundle["modules"]["life-chart"]["enabled"] is True, "life-chart public execution missing")
for module in ("bazi", "ziwei", "yijing", "past-life", "bardo", "relationship"):
    require(bundle["modules"][module]["enabled"] is False, f"interpretive module enabled: {module}")
require(cases["case_count"] == 48 and len(cases["cases"]) == 48, "48 synthetic cases required")
require(cases["classification"] == "synthetic_conformance", "cases cannot claim reality validation")
for table in ("life_trend_executions","life_trend_buckets","life_trend_timing_windows","life_trend_replay_records","life_trend_execution_comparisons"):
    require(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in migration, f"FORCE RLS missing: {table}")
require("float(" not in engine and "Decimal(" not in engine, "binary float/undeclared Decimal forbidden")
require('"no_interpolation": True' in engine, "gap interpolation gate missing")
require("execute(request)" in api and 'replay(row["replay_manifest"]' in api, "thin API public-engine calls missing")
for forbidden in ("DeepSeekProvider", "urllib.request", "requests.", "httpx.", "oracle_adapter"):
    require(forbidden not in engine, f"provider entered core: {forbidden}")
require("core_output_hash" in migration and "narrative_output_hash" in migration, "core/AI hash separation missing")
print("Sprint 18 life-trend static gates passed")
