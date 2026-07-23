RESTRICTED = {"copyright_restricted", "practice_restricted", "sealed", "unknown"}
SEARCH_HIDDEN = {"rejected", "retired"}


def validate_claim(claim: dict, document: dict) -> list[str]:
    errors = []
    access = claim["access_class"]
    uses = claim["allowed_uses"]
    locator = claim.get("locator") or {}
    if claim["confidence"] == "verified" and not any(locator.values()):
        errors.append("verified_claim_requires_precise_locator")
    if document["knowledge_layer"] == "system_interpretation" and claim["claim_type"] == "traditional_statement":
        errors.append("system_interpretation_cannot_be_traditional_statement")
    if access in {"sealed", "practice_restricted", "copyright_restricted"} and claim.get("source_excerpt"):
        errors.append("restricted_content_must_not_store_excerpt")
    if access in RESTRICTED and (uses.get("rag") or uses.get("rule_authoring")):
        errors.append("restricted_or_unknown_not_allowed_for_rag_or_rules")
    return errors


def validate_research_rule(rule: dict, claims: list[dict]) -> list[str]:
    errors = []
    if rule["status"] == "active":
        errors.append("sprint1b2_forbids_active_rules")
    if rule["status"] in {"reviewed", "approved"} and not rule.get("counter_conditions"):
        errors.append("reviewed_rule_requires_counterevidence")
    if not rule.get("missing_data_behavior"):
        errors.append("missing_data_behavior_required")
    if not claims:
        errors.append("rule_requires_claim_basis")
    if any(c.get("review_status") != "approved" for c in claims):
        errors.append("rule_cannot_use_unapproved_claim")
    if rule.get("method_id") == "UNCONFIRMED" and rule["status"] == "active":
        errors.append("unconfirmed_rule_cannot_be_active")
    if rule.get("production_activatable"):
        errors.append("sprint1b2_production_activatable_must_be_false")
    return errors


def archetype_errors(records: list[dict]) -> list[str]:
    banned = {"佛菩萨转世", "高僧转世", "皇帝", "公主", "名人身份"}
    errors = []
    for item in records:
        text = str(item)
        if any(term in text for term in banned):
            errors.append(f"named_or_privileged_identity_forbidden:{item.get('name')}")
        for key in ("positive_evidence", "counterevidence", "ordinary_explanations", "misjudgment_risks"):
            if not item.get(key):
                errors.append(f"archetype_required_field:{key}:{item.get('name')}")
    if records:
        ordinary = sum(item.get("category") == "ordinary_livelihood" for item in records)
        if ordinary * 4 < len(records):
            errors.append("ordinary_livelihood_below_one_quarter")
    return errors
