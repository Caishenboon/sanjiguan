"""Static release gate for the research-only BaZi structure foundation."""
from __future__ import annotations

import json
from pathlib import Path

from sanji_engine import inspect_ruleset
from sanji_engine.canonical import content_hash

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/bazi/traditional-structure-mechanical-reference-v1.json"
DOC = ROOT / "docs/methods/bazi-traditional-structure-foundation-v1.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


asset = json.loads(REFERENCE.read_text(encoding="utf-8"))
require(asset["classification"] == "mechanical_reference", "reference must not claim authority-golden status")
require(asset["authority_status"] == "NOT_AUTHORITY_GOLDEN", "authority status drift")
require(asset["declared_case_count"] == 166, "reference case count drift")
require(content_hash(asset) == "sha256:a81019a737762808cb29636b06753cbcf18582d968be107df428287f7463f25b", "reference aggregate hash drift")

bundle = inspect_ruleset("bazi-traditional-structure-research-1.0.0")
bazi = bundle["modules"]["bazi"]
require(bundle["status"] == "research_active", "structure ruleset must remain research_active")
require(bazi["review_status"] == "UNCONFIRMED", "structure review must remain UNCONFIRMED")
require(not bundle["production_activatable"] and not bazi["production_activatable"], "structure ruleset must not become production activatable")
require(not bazi["interpretation_enabled"], "traditional interpretation must remain disabled")
require(not bundle["modules"]["ziwei"]["enabled"] and not bundle["modules"]["yijing"]["enabled"], "unrelated systems must remain disabled")

text = DOC.read_text(encoding="utf-8")
require("传统结构研究结果，不等于完整八字论命。" in text, "required research disclaimer missing")
for forbidden in ("完整八字论命已实现", "权威 Golden", "合化结论", "成局结论"):
    require(forbidden not in text, f"misleading claim present: {forbidden}")

print("BaZi traditional-structure research gate passed: 166 references, no interpretation activation.")
