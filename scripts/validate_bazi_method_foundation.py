"""Static and deterministic gates for the BaZi method foundation Sprint."""
from __future__ import annotations

import ast
from pathlib import Path

from sanji_engine import execute, inspect_ruleset
from sanji_engine.bazi import (
    list_profiles,
    load_boundary_cases,
    load_evidence_bundle,
    run_conformance,
)

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise SystemExit(f"bazi method foundation gate failed: {message}")


def request() -> dict:
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": "bazi-method-foundation-gate",
        "run_mode": "research_preview",
        "requested_modules": ["bazi"],
        "input_snapshot": {
            "operation": "bazi_method_conformance",
            "bazi_method_profile_id": "BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1",
            "synthetic": True,
        },
        "ruleset_bundle_id": "bazi-method-foundation-0.1.0",
        "data_versions": {
            "tzdb": "2025b",
            "ephemeris": "astronomy-engine-2.1.19",
            "calendar_dataset": "calendar-migration-baseline-1.0.0",
            "bazi_method_profiles": "bazi-method-profile-registry/1.0.0",
        },
        "deterministic_context": {
            "as_of": "2026-07-27T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
    }


def main() -> None:
    profiles = list_profiles()
    evidence = load_evidence_bundle()
    cases = load_boundary_cases()
    result = run_conformance([item["profile_id"] for item in profiles])

    if len(profiles) != 3:
        fail("expected three discriminating profiles")
    if len(evidence["claims"]) != 12 or len(evidence["locators"]) != 10:
        fail("evidence inventory count drift")
    if cases["case_count"] != 74:
        fail("boundary case count drift")
    if result["calculation_performed"] or result["pillar_results"] is not None:
        fail("conformance result contains a pillar calculation")

    ruleset = inspect_ruleset("bazi-method-foundation-0.1.0")
    bazi = ruleset["modules"]["bazi"]
    if bazi["enabled"] or bazi["production_activatable"]:
        fail("BaZi ruleset is active")
    executed = execute(request())["module_results"]["bazi"]
    if executed["error"]["code"] != "MODULE_DISABLED" or executed["result"] is not None:
        fail("BaZi execution did not remain structurally disabled")

    forbidden = {
        "calculate_year_pillar", "calculate_month_pillar",
        "calculate_day_pillar", "calculate_hour_pillar",
        "calculate_ten_gods", "calculate_strength", "calculate_luck_cycles",
    }
    for path in (ROOT / "packages/sanji-engine/src/sanji_engine/bazi").rglob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        definitions = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        if definitions & forbidden:
            fail(f"forbidden pillar algorithm in {path}")

    print(
        "BaZi method foundation passed: "
        f"{len(profiles)} profiles, {len(evidence['claims'])} claims, "
        f"{len(evidence['locators'])} locators, {cases['case_count']} cases, "
        f"hash {result['content_hash']}"
    )


if __name__ == "__main__":
    main()
