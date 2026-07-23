VALID_STATES = {
    "not_filled", "not_applicable", "unknown", "explicit_none",
    "filled_low_reliability", "filled_high_reliability",
}
DOMAINS = ("ming", "dream", "sensation", "karma", "vow", "relation", "life_event")


def completeness_state(answer_state: str, reliability_score: float | None = None) -> str:
    if answer_state in {"not_filled", "not_applicable", "unknown", "explicit_none"}:
        return answer_state
    if answer_state != "filled" or reliability_score is None:
        raise ValueError("invalid_completeness_input")
    return "filled_high_reliability" if reliability_score >= 0.7 else "filled_low_reliability"


def summarize_completeness(states: dict[str, str]) -> dict:
    if set(states) != set(DOMAINS) or any(value not in VALID_STATES for value in states.values()):
        raise ValueError("all_completeness_domains_required")
    sufficient = sum(value in {"explicit_none", "not_applicable", "filled_high_reliability",
                               "filled_low_reliability"} for value in states.values())
    return {"dimensions": states, "completed_dimensions": sufficient,
            "total_dimensions": len(DOMAINS),
            "meaning": "data_readiness_only_not_fortune_or_spiritual_score"}
