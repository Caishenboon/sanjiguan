"""Static and deterministic gates for Liuxiang research platform v1."""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jsonschema import Draft202012Validator
from sanji_engine import inspect_ruleset
from sanji_engine.canonical import content_hash
from sanji_engine.inference.liuxiang_v1 import load_liuxiang_assets, run_liuxiang_research_v1
from packages.research_data.core import load_manifests, validate_manifest

ENGINE = ROOT / "packages/sanji-engine/src/sanji_engine"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"liuxiang research v1 gate failed: {message}")


bundle = inspect_ruleset("liuxiang-research-v1.0.0")
require(bundle["status"] == "research_active", "bundle must be research_active")
require(bundle["review_status"] == "UNCONFIRMED", "review status drift")
require(bundle["production_activatable"] is False, "production activation forbidden")
for module in ("signals", "inference"):
    require(bundle["modules"][module]["enabled"] is True, f"{module} research module disabled")
    require(bundle["modules"][module]["production_activatable"] is False, f"{module} production enabled")
for module in ("bazi", "ziwei", "yijing", "past-life", "bardo", "relationship", "life-chart"):
    require(bundle["modules"][module]["enabled"] is False, f"{module} must remain disabled")
    require(bundle["modules"][module]["status"] == "draft", f"{module} status drift")

dimensions, mappings, policy = load_liuxiang_assets()
require(len(dimensions["dimensions"]) == 6, "exactly six current dimensions required")
require(
    [value["dimension_id"] for value in dimensions["dimensions"]]
    == ["lx_ming", "lx_ye", "lx_yuan", "lx_meng", "lx_yuan_relation", "lx_shi"],
    "stable dimension IDs drift",
)
require(dimensions["disputed_definitions"][0]["activation"] == "disabled", "感应象 dispute activated")
active_mappings = [
    value for value in mappings["rules"] if value["activation_status"] == "research_active"
]
require(
    [value["mapping_rule_id"] for value in active_mappings]
    == ["LX.SYNTHETIC.CONFORMANCE.V1"],
    "only synthetic mapping may be active",
)
for value in mappings["rules"]:
    require(value["production_activatable"] is False, "mapping production flag drift")

for path in (
    ENGINE / "signals/v2.py",
    ENGINE / "signals/adapters.py",
    ENGINE / "inference/liuxiang_v1.py",
):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    require(not any(isinstance(node, ast.Constant) and isinstance(node.value, float) for node in ast.walk(tree)),
            f"binary float literal in {path.name}")
    text = path.read_text(encoding="utf-8")
    for forbidden in ("DeepSeek", "oracle_adapters", "requests.", "httpx."):
        require(forbidden not in text, f"forbidden core dependency {forbidden}")

asset = json.loads(
    (ENGINE / "golden_cases/liuxiang/synthetic-conformance-v1.json").read_text(encoding="utf-8")
)
require(asset["asset_class"] == "synthetic_conformance", "case asset class drift")
require(asset["reality_validation"] is False, "synthetic cases claim reality validation")
require(len(asset["cases"]) == 100, "100 synthetic cases required")
hashes = []
for case in asset["cases"]:
    result, _ = run_liuxiang_research_v1(case["snapshot"])
    require(result["status"] == case["expected_status"], f"status mismatch: {case['case_id']}")
    hashes.append({"case_id": case["case_id"], "result_hash": result["result_hash"]})
require(content_hash(hashes) == asset["aggregate_hash"], "100-case aggregate hash drift")

legacy = json.loads(
    (ROOT / "tests/fixtures/signals-inference-research-baseline.json").read_text(encoding="utf-8")
)
require(
    legacy["aggregate_hash"]
    == "a08cb815b1ba65f16c4873b4c6cfac6653220a7d5630078a654beb36935ea96c",
    "legacy 30-case hash drift",
)

schema_dir = ENGINE / "schemas/v2"
signal_schema = json.loads((schema_dir / "signal-v2.schema.json").read_text(encoding="utf-8"))
result_schema = json.loads((schema_dir / "liuxiang-result.schema.json").read_text(encoding="utf-8"))
expanded_result_schema = json.loads(json.dumps(result_schema))
expanded_result_schema["properties"]["signals"]["items"] = signal_schema
expanded_result_schema["properties"]["effective_signals"]["items"] = signal_schema
result, _ = run_liuxiang_research_v1(asset["cases"][0]["snapshot"])
Draft202012Validator(expanded_result_schema).validate(result)
Draft202012Validator(signal_schema).validate(result["signals"][0])

for manifest in load_manifests():
    require(not validate_manifest(manifest), f"invalid dataset manifest: {manifest['dataset_id']}")
dreambank = next(value for value in load_manifests() if value["dataset_id"].startswith("DReAMy"))
require(dreambank["connector_enabled"] is False, "DreamBank connector enabled")
require(dreambank["raw_data_committable"] is False, "DreamBank raw data committable")
vedastro = [value for value in load_manifests() if value["dataset_id"].startswith("vedastro-org/")]
require({value["shared_source_group"] for value in vedastro} == {"vedastro_org"},
        "VedAstro datasets treated as independent providers")

migration = (ROOT / "infra/migrations/0015_liuxiang_research_platform_v1.sql").read_text(encoding="utf-8")
for table in (
    "research_dataset_manifests", "research_import_runs", "research_quality_reports",
    "normalized_research_people", "research_life_events", "research_person_matches",
    "liuxiang_research_executions", "liuxiang_research_signals",
    "liuxiang_research_candidates",
):
    require(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in migration, f"FORCE RLS missing: {table}")

api_source = (ROOT / "apps/api/app/liuxiang_research_routes.py").read_text(encoding="utf-8")
require("from sanji_engine import execute, replay" in api_source, "API must call the engine contract")
for forbidden in ("confidence_weights", "status_thresholds", "magnitude_bp *"):
    require(forbidden not in api_source, f"API contains duplicated scoring logic: {forbidden}")
openapi = json.loads(
    (ROOT / "docs/api/liuxiang-research.openapi.json").read_text(encoding="utf-8")
)
required_paths = {
    "/api/v1/admin/research/liuxiang/sources",
    "/api/v1/admin/research/liuxiang/quality",
    "/api/v1/admin/research/liuxiang/matching",
    "/api/v1/admin/research/liuxiang/aggregate-report",
    "/api/v1/admin/research/liuxiang/executions",
    "/api/v1/admin/research/liuxiang/executions/{execution_id}",
    "/api/v1/admin/research/liuxiang/executions/{execution_id}/candidates",
    "/api/v1/admin/research/liuxiang/executions/{execution_id}/evidence",
    "/api/v1/admin/research/liuxiang/executions/{execution_id}/trace",
    "/api/v1/admin/research/liuxiang/executions/{execution_id}/replay",
    "/api/v1/admin/research/liuxiang/compare",
}
require(required_paths <= set(openapi["paths"]), "thin API contract incomplete")
for page in (
    ROOT / "apps/web/app/admin/research/liuxiang/page.tsx",
    ROOT / "apps/web/app/admin/research/data-sources/page.tsx",
    ROOT / "apps/web/app/admin/research/controls/page.tsx",
):
    text = page.read_text(encoding="utf-8")
    for forbidden in ("confidence_weights", "status_thresholds", "mapping_reliability_bp"):
        require(forbidden not in text, f"frontend scoring copy: {page.name}:{forbidden}")

excluded = {".git", "node_modules", ".next", "work", "storybook-static", ".cache", ".venv"}
for directory, children, filenames in os.walk(ROOT):
    children[:] = [name for name in children if name not in excluded]
    for filename in filenames:
        path = Path(directory, filename)
        if path.suffix.lower() not in {".py", ".ts", ".tsx", ".md", ".json", ".yml", ".yaml", ".sql"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        require(
            re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/](?:Users|Documents)[\\/]", text) is None,
            f"local absolute path: {path}",
        )

print(
    "Liuxiang research v1 gate passed: "
    f"6 dimensions, 100 synthetic cases, aggregate {asset['aggregate_hash']}."
)
