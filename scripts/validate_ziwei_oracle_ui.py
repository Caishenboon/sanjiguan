"""Static gates for Ziwei research, Oracle isolation, and the Sanji UI system."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "packages/sanji-engine/src/sanji_engine"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ziwei/oracle/ui gate failed: {message}")


bundle = json.loads((ENGINE / "rulesets/ziwei-sanhe-research-1.0.0.json").read_text(encoding="utf-8"))
ziwei = bundle["modules"]["ziwei"]
require(bundle["status"] == "research_active", "Ziwei bundle must remain research_active")
require(ziwei["review_status"] == "UNCONFIRMED", "Ziwei must remain UNCONFIRMED")
require(ziwei["enabled"] is True, "research execution must be explicit and enabled in its isolated bundle")
require(ziwei["production_activatable"] is False, "Ziwei must not be production activatable")
require(ziwei["interpretation_enabled"] is False, "Ziwei interpretation must be disabled")
require(
    ziwei["source_claim_asset_version"] == "ziwei-source-claim-registry/1.0.0",
    "Ziwei source-claim asset version drift",
)

profiles = json.loads((ENGINE / "ziwei/assets/profiles-1.0.0.json").read_text(encoding="utf-8"))
require(len(profiles["profiles"]) >= 2, "at least two explicit Ziwei research Profiles required")
source_claims = json.loads(
    (ENGINE / "ziwei/assets/source-claims-1.0.0.json").read_text(encoding="utf-8")
)
require(source_claims["review_status"] == "UNCONFIRMED", "source claims review status drift")
require(not source_claims["production_activatable"], "source claims production activation drift")
claim_ids = {claim["claim_id"] for claim in source_claims["claims"]}
for profile in profiles["profiles"]:
    require(profile["review_status"] == "UNCONFIRMED", "Profile review status drift")
    require(not profile["production_activatable"], "Profile production activation drift")
    require("default" not in profile["profile_id"].lower(), "default Profile is forbidden")
    require(set(profile["source_claims"]) <= claim_ids, "Profile references an unknown source claim")
for claim in source_claims["claims"]:
    require(claim["traditional_source"] is None, "unreviewed claim must not assert a traditional source")
    require(
        claim["authority_status"] == "SOURCE_AND_LINEAGE_REVIEW_REQUIRED",
        "unreviewed source claim authority drift",
    )

root_public = (ENGINE / "__init__.py").read_text(encoding="utf-8")
require(
    '__all__ = ["validate_request", "execute", "replay", "inspect_ruleset"]' in root_public,
    "sanji-engine root API surface changed",
)

oracle_root = ROOT / "packages/oracle-adapters"
for name in ("third-party-lock.json", "THIRD_PARTY_NOTICES.md"):
    require((ROOT / name).exists(), f"{name} missing")
lock = json.loads((ROOT / "third-party-lock.json").read_text(encoding="utf-8"))
names = {item["name"] for item in lock["dependencies"]}
require(
    {
        "lunar-python",
        "tyme4py",
        "sxtwl",
        "iztro",
        "storybook",
        "@playwright/test",
        "@lhci/cli",
    }
    <= names,
    "third-party lock incomplete",
)
contract = (oracle_root / "src/oracle_adapters/common/contract.py").read_text(encoding="utf-8")
require("production_allowed\": False" in contract, "Oracle production boundary missing")
for forbidden in ("from oracle_adapters", "import oracle_adapters", "DeepSeek", "DEEPSEEK"):
    for path in ENGINE.rglob("*.py"):
        require(forbidden not in path.read_text(encoding="utf-8"), f"forbidden Engine dependency: {forbidden}")

ui = ROOT / "packages/sanji-ui"
required_components = (
    "SanjiShell", "SanjiHeader", "ResearchNavigation", "VerdictStatusBadge",
    "RulesetBadge", "ProfileBadge", "EvidenceCard", "CounterEvidenceCard",
    "TraceStep", "HashPanel", "VersionPanel", "EmptyState", "ErrorState",
    "YijingHexagram", "BaziFourPillars", "ZiweiPalaceGrid",
    "OracleDiffPanel", "ResearchWarning", "ConsentPanel",
)
source = (ui / "src/index.tsx").read_text(encoding="utf-8")
for component in required_components:
    require(f"function {component}" in source, f"UI component missing: {component}")
require((ROOT / "docs/design/sanji-visual-language.md").exists(), "visual language missing")
require((ROOT / "apps/web/playwright.config.ts").exists(), "Playwright config missing")
require((ROOT / "apps/web/lighthouserc.json").exists(), "Lighthouse config missing")

excluded = {".git", "node_modules", ".next", "work", "storybook-static"}
for directory, children, filenames in os.walk(ROOT):
    children[:] = [name for name in children if name not in excluded]
    for filename in filenames:
        path = Path(directory, filename)
        if path.suffix.lower() in {".py", ".ts", ".tsx", ".md", ".json", ".yml", ".yaml", ".sql"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            require(
                re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/](?:Users|Documents)[\\/]", text) is None,
                f"local absolute path: {path}",
            )

print("Ziwei research, Oracle isolation, third-party, and Sanji UI gates passed")
