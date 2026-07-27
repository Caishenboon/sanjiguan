"""Static release gates for the sanji-engine boundary foundation."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages/sanji-engine/src/sanji_engine"
PUBLIC = {"validate_request", "execute", "replay", "inspect_ruleset"}


def fail(message: str) -> None:
    raise SystemExit(f"sanji-engine gate failed: {message}")


def main() -> None:
    import sanji_engine

    if set(sanji_engine.__all__) != PUBLIC:
        fail("public API differs from Engine API 1.0")

    forbidden_imports = {
        "fastapi", "psycopg", "sqlalchemy", "requests", "httpx", "openai"
    }
    for path in CORE.rglob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom):
                module = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in forbidden_imports:
                        fail(f"forbidden import {alias.name} in {path}")
            if module and module.split(".")[0] in forbidden_imports:
                fail(f"forbidden import {module} in {path}")

    for root in (ROOT / "apps", ROOT / "packages/engine"):
        for path in root.rglob("*.py"):
            text = path.read_text("utf-8")
            if "sanji_engine." in text and "sanji_engine.public" not in text:
                fail(f"application imports an internal engine module: {path}")

    adapter = ROOT / "packages/research_inference/engine.py"
    adapter_tree = ast.parse(adapter.read_text("utf-8"))
    forbidden_adapter_names = {
        "DOMAIN_WEIGHTS", "score_candidate", "normalize_weights",
        "build_candidates", "decide_verdict", "rank_candidates",
    }
    defined = {
        node.name for node in ast.walk(adapter_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    assigned = {
        target.id
        for node in ast.walk(adapter_tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else [node.target]
        )
        if isinstance(target, ast.Name)
    }
    leaked = sorted((defined | assigned) & forbidden_adapter_names)
    if leaked:
        fail(f"legacy adapter contains algorithm definitions: {leaked}")

    bundle = sanji_engine.inspect_ruleset("core-boundary-0.1.0")
    prohibited = (
        "bazi", "ziwei", "yijing", "past-life", "bardo",
        "relationship", "life-chart",
    )
    for module in prohibited:
        item = bundle["modules"][module]
        if item["enabled"] or item["status"] != "draft":
            fail(f"{module} is not draft + disabled")

    research = sanji_engine.inspect_ruleset("research-baseline-0.2.0")
    if research["status"] != "research_active" or research["production_activatable"]:
        fail("research baseline is not explicitly non-production")
    for module in ("signals", "inference"):
        item = research["modules"][module]
        if (
            not item["enabled"]
            or item["baseline_class"] != "research_baseline"
            or item["production_activatable"]
        ):
            fail(f"{module} research-baseline gate is invalid")

    baseline = json.loads(
        (CORE / "research_baselines/signals-inference-sprint2.json").read_text("utf-8")
    )
    if baseline["baseline_class"] != "research_baseline":
        fail("Signals/Inference fixture is mislabeled")
    print("sanji-engine boundary, ruleset and dependency gates passed")


if __name__ == "__main__":
    main()
