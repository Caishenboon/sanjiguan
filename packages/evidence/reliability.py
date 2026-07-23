"""Record reliability only. This module makes no metaphysical inference."""

SOURCE_BASE = {
    "document": 0.72, "repeated_observation": 0.62, "family_memory": 0.48,
    "self_memory": 0.44, "single_event": 0.32,
}


def assess_reliability(item: dict) -> dict:
    score = SOURCE_BASE[item["source_type"]]
    support, weaken = [f"source:{item['source_type']}"], []
    if item.get("frequency", 0) >= 3:
        score += 0.08; support.append("long_term_repetition")
    if item.get("first_observed_age") is not None and item["first_observed_age"] <= 12:
        score += 0.06; support.append("childhood_onset")
    if item.get("independent_corroboration"):
        score += 0.10; support.append("independent_corroboration")
    if item.get("specific_description"):
        score += 0.05; support.append("specific_description")
    ordinary = item.get("possible_ordinary_explanations", [])
    if ordinary:
        score -= min(0.18, 0.04 * len(ordinary)); weaken.append("ordinary_explanations_present")
    if item.get("frequency", 0) <= 1:
        score -= 0.06; weaken.append("single_or_rare_observation")
    if item.get("memory_reshaping_risk"):
        score -= 0.10; weaken.append("memory_reshaping_risk")
    score = round(max(0, min(1, score)), 3)
    level = "high" if score >= 0.7 else "medium" if score >= 0.45 else "low"
    return {"reliability_score": score, "reliability_level": level,
            "supporting_factors": support, "weakening_factors": weaken,
            "meaning": "record_reliability_only_not_past_life_evidence"}
