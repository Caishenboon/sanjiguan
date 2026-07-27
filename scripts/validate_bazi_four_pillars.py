"""Fail-closed static and deterministic gate for BaZi mechanical research."""
from pathlib import Path

from sanji_engine import inspect_ruleset
from sanji_engine.bazi.conformance import load_boundary_cases
from sanji_engine.bazi.profiles import execution_profile_registry

ROOT = Path(__file__).resolve().parents[1]
required = [
    "packages/sanji-engine/src/sanji_engine/bazi/four_pillars.py",
    "packages/sanji-engine/src/sanji_engine/bazi/assets/execution-profiles-1.0.0.json",
    "packages/sanji-engine/src/sanji_engine/bazi/assets/day-epoch-1.0.0.json",
    "packages/shared-types/schemas/bazi-four-pillars-engine-result.schema.json",
    "infra/migrations/0013_bazi_four_pillars_research.sql",
    "apps/api/app/bazi_research_routes.py",
    "apps/web/components/BaziResearchPreview.tsx",
    "docs/architecture/bazi-four-pillars-engine.md",
    "docs/sprints/bazi-four-pillars-engine.md",
]
missing = [path for path in required if not (ROOT / path).exists()]
if missing:
    raise SystemExit(f"BaZi four-pillar delivery files missing: {missing}")

registry = execution_profile_registry()
if len(registry["profiles"]) != 3 or registry["production_activatable"]:
    raise SystemExit("BaZi execution profiles crossed the research-only gate")
if any(profile["profile_version"] != "1.0.0" for profile in registry["profiles"]):
    raise SystemExit("BaZi execution profile version drift")

bundle = inspect_ruleset("bazi-four-pillars-research-1.0.0")
if bundle["status"] != "research_active" or bundle["production_activatable"]:
    raise SystemExit("BaZi ruleset is not research-only")
if not bundle["modules"]["bazi"]["enabled"]:
    raise SystemExit("BaZi mechanical module is unexpectedly disabled")
if bundle["modules"]["bazi"]["interpretation_enabled"]:
    raise SystemExit("BaZi interpretation must remain disabled")

for module in ("ziwei", "yijing", "signals", "inference", "past-life", "bardo",
               "relationship", "life-chart"):
    if bundle["modules"][module]["enabled"]:
        raise SystemExit(f"out-of-scope module activated: {module}")

if load_boundary_cases()["case_count"] != 74:
    raise SystemExit("BaZi boundary-case asset count drift")

application = "\n".join(
    (ROOT / path).read_text("utf-8")
    for path in (
        "apps/api/app/bazi_research_routes.py",
        "apps/web/components/BaziResearchPreview.tsx",
    )
)
for forbidden in ("STEMS =", "BRANCHES =", "calculate_day_pillar",
                  "calculate_month_pillar", "calculate_hour_pillar"):
    if forbidden in application:
        raise SystemExit(f"algorithm duplicated outside sanji-engine: {forbidden}")

print("BaZi four-pillar gate passed: 3 explicit UNCONFIRMED profiles; 74 boundary assets; no production interpretation.")
