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

    bundle = sanji_engine.inspect_ruleset("core-boundary-0.1.0")
    prohibited = (
        "bazi", "ziwei", "yijing", "past-life", "bardo",
        "relationship", "life-chart",
    )
    for module in prohibited:
        item = bundle["modules"][module]
        if item["enabled"] or item["status"] != "draft":
            fail(f"{module} is not draft + disabled")

    baseline = json.loads(
        (CORE / "research_baselines/signals-inference-sprint2.json").read_text("utf-8")
    )
    if baseline["baseline_class"] != "research_baseline":
        fail("Signals/Inference fixture is mislabeled")
    print("sanji-engine boundary, ruleset and dependency gates passed")


if __name__ == "__main__":
    main()
