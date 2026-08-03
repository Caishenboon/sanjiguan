from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "methods" / "rule-audit-v1.json"

REQUIRED = {
    "rule_id", "system", "layer", "current_implementation", "code_location",
    "current_ruleset_version", "method_or_school", "source_type", "source_reference",
    "source_reliability", "consensus_status", "dispute_summary", "supported_profiles",
    "implementation_status", "test_status", "golden_status", "production_status",
    "impact_if_changed", "replay_compatibility", "copyright_or_license_note", "reviewer_note",
}
CONSENSUS = {"CONSENSUS_MECHANICAL", "SCHOOL_SPECIFIC", "DISPUTED", "UNCONFIRMED", "NOT_IMPLEMENTED", "SANJI_ORIGINAL"}
PRODUCTION = {"PRODUCTION_CONFIRMED", "PROFILE_REQUIRED", "RESEARCH_ONLY", "DISABLED"}
LAYERS = {"mechanical", "traditional_interpretation", "sanji_original"}


def validate() -> list[str]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    errors: list[str] = []
    seen: set[str] = set()
    for index, rule in enumerate(data.get("rules", [])):
        missing = REQUIRED - rule.keys()
        if missing:
            errors.append(f"rules[{index}] missing: {sorted(missing)}")
        rule_id = rule.get("rule_id", "")
        if rule_id in seen:
            errors.append(f"duplicate rule_id: {rule_id}")
        seen.add(rule_id)
        if rule.get("consensus_status") not in CONSENSUS:
            errors.append(f"{rule_id}: invalid consensus_status")
        if rule.get("production_status") not in PRODUCTION:
            errors.append(f"{rule_id}: invalid production_status")
        if rule.get("layer") not in LAYERS:
            errors.append(f"{rule_id}: invalid layer")
        location = rule.get("code_location", "").split("::", 1)[0]
        if location and location != "none" and not (ROOT / location).exists():
            errors.append(f"{rule_id}: missing code location {location}")
        if rule.get("consensus_status") == "NOT_IMPLEMENTED" and rule.get("production_status") != "DISABLED":
            errors.append(f"{rule_id}: non-implemented rule must be disabled")
        if rule.get("layer") == "sanji_original" and rule.get("consensus_status") != "SANJI_ORIGINAL":
            errors.append(f"{rule_id}: Sanji layer must be labeled SANJI_ORIGINAL")
    if not seen:
        errors.append("registry contains no rules")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"traditional method audit valid: {REGISTRY.relative_to(ROOT)}")
