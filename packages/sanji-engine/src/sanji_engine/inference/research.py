"""Behavior-equivalent migration of the 0.1.0 research inference baseline.

Binary floats remain deliberately isolated here to preserve the frozen legacy
results. They are converted to decimal strings at the Engine contract boundary.
This is migration compatibility, not a new or production-approved algorithm.
"""
from __future__ import annotations

import hashlib
import json
import math

from ..signals import deduplicate_signals, validate_signals

DOMAIN_WEIGHTS = {
    "ming": 0.20,
    "karma": 0.20,
    "vow": 0.20,
    "dream": 0.15,
    "relation": 0.10,
    "life_event": 0.10,
    "sensation": 0.05,
}
LEGACY_STAGES = (
    "normalize_input", "collect_evidence", "build_signals", "generate_candidates",
    "score_candidates", "apply_counterevidence", "detect_conflicts",
    "rank_hypotheses", "cluster_past_life_nodes", "build_retrieval_query",
    "retrieve_claims", "lock_engine_verdict", "generate_prose", "validate_output",
    "persist_report",
)


def legacy_stable_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def normalize_weights(domains: set[str]) -> dict[str, float]:
    enabled = {d: w for d, w in DOMAIN_WEIGHTS.items() if d in domains and d != "gua"}
    if not enabled:
        return {}
    total = sum(enabled.values())
    normalized = {d: min(0.40, w / total) for d, w in enabled.items()}
    scale = sum(normalized.values())
    return {d: v / scale for d, v in normalized.items()}


def contribution(signal: dict, weights: dict[str, float]) -> float:
    direction = 1 if signal["direction"] == "support" else -1
    ordinary_discount = 0.7 if signal.get("ordinary_explanation_present") else 1
    return (
        direction
        * signal["strength"]
        * signal["source_reliability"]
        * signal["relevance"]
        * weights.get(signal["domain"], 0)
        * ordinary_discount
    )


def score_candidate(
    candidate: dict, signals: list[dict], weights: dict, config: dict
) -> dict:
    relevant = [signal for signal in signals if signal["tag"] in candidate["tags"]]
    components = [
        {"signal_id": signal["id"], "value": round(contribution(signal, weights), 8)}
        for signal in relevant
    ]
    positive = sum(item["value"] for item in components if item["value"] > 0)
    negative = -sum(item["value"] for item in components if item["value"] < 0)
    signal_tags = {signal["tag"] for signal in signals}
    hard = [
        conflict
        for conflict in candidate.get("hard_conflicts", [])
        if conflict in signal_tags
    ]
    raw = positive - negative
    raw -= config["counterevidence_penalty"] * negative
    raw -= config["hard_conflict_penalty"] * len(hard)
    raw -= config["grandiosity_penalty"] if candidate.get("grandiosity_risk") else 0
    independent_domains = {
        signal["domain"] for signal in relevant if signal["direction"] == "support"
    }
    if len(independent_domains) >= 3:
        raw += config["cross_system_bonus"]
    strength = round(
        100 / (1 + math.exp(-(config["calibration_a"] * raw + config["calibration_b"])))
    )
    return {
        **candidate,
        "raw_score": round(raw, 8),
        "strength": strength,
        "supporting_evidence": [
            signal["id"] for signal in relevant if signal["direction"] == "support"
        ],
        "counterevidence": [
            signal["id"] for signal in relevant if signal["direction"] == "oppose"
        ],
        "hard_conflicts": hard,
        "ordinary_explanations": [
            signal["id"]
            for signal in relevant
            if signal.get("ordinary_explanation_present")
        ],
        "missing_critical_data": candidate.get("missing_critical_data", []),
        "net_effect": round(positive - negative, 8),
        "contributions": components,
        "independent_domains": sorted(independent_domains),
    }


def verdict(ranked: list[dict], completeness: float, config: dict) -> tuple[str, dict]:
    if not ranked or completeness < config["minimum_completeness"]:
        return "insufficient", {
            "reason": "minimum_completeness",
            "completeness": completeness,
            "threshold": config["minimum_completeness"],
        }
    first = ranked[0]
    second = ranked[1] if len(ranked) > 1 else {"strength": 0}
    margin = first["strength"] - second["strength"]
    if first["hard_conflicts"]:
        return "contested", {"reason": "top_candidate_hard_conflict", "margin": margin}
    if (
        first["strength"] >= config["decisive_strength"]
        and len(first["independent_domains"]) >= 3
        and margin >= config["decisive_margin"]
    ):
        return "decisive", {"reason": "decisive_thresholds_met", "margin": margin}
    if margin < config["contested_margin"]:
        return "contested", {"reason": "contested_margin", "margin": margin}
    return "provisional", {"reason": "provisional_fallback", "margin": margin}


def run_research_baseline(
    case: dict, archetypes: list[dict], config: dict
) -> dict:
    if case.get("mode") != "research_preview" or not case.get(
        "synthetic_or_research"
    ):
        raise ValueError("research_preview_owner_fixture_or_research_profile_required")
    validated = validate_signals(case.get("signals"))
    signals, deduplication = deduplicate_signals(validated)
    weights = normalize_weights({signal["domain"] for signal in signals})
    signal_tags = {signal["tag"] for signal in signals}
    candidates = [
        archetype
        for archetype in archetypes
        if set(archetype.get("tags", [])) & signal_tags
    ]
    candidate_generation = [
        {"candidate_id": item["id"], "basis": "tag_match"} for item in candidates
    ]
    for archetype in archetypes:
        if len(candidates) >= 5:
            break
        if archetype not in candidates:
            candidates.append(archetype)
            candidate_generation.append(
                {"candidate_id": archetype["id"], "basis": "asset_order_fill"}
            )
    ordinary = [
        archetype
        for archetype in archetypes
        if archetype["category"] == "ordinary_livelihood"
    ]
    if ordinary and not any(
        archetype["category"] == "ordinary_livelihood" for archetype in candidates
    ):
        candidates.append(ordinary[0])
        candidate_generation.append(
            {"candidate_id": ordinary[0]["id"], "basis": "ordinary_guard"}
        )
    scored = [
        score_candidate(candidate, signals, weights, config)
        for candidate in candidates[:20]
    ]
    ranked = sorted(scored, key=lambda item: (-item["raw_score"], item["id"]))[:5]
    if ordinary and not any(
        hypothesis["category"] == "ordinary_livelihood" for hypothesis in ranked
    ):
        ordinary_scored = sorted(
            (
                hypothesis
                for hypothesis in scored
                if hypothesis["category"] == "ordinary_livelihood"
            ),
            key=lambda item: (-item["raw_score"], item["id"]),
        )
        if ordinary_scored:
            ranked[-1] = ordinary_scored[0]
        ranked = sorted(ranked, key=lambda item: (-item["raw_score"], item["id"]))
    for index, item in enumerate(ranked, 1):
        item["rank"] = index
    status, status_reason = verdict(
        ranked, float(case.get("completeness", 0)), config
    )
    nodes = [
        {
            "node_type": (
                "ordinary_continuity"
                if hypothesis["category"] == "ordinary_livelihood"
                else "root_pattern"
            ),
            "primary_archetype_id": hypothesis["id"],
            "secondary_archetype_ids": [],
            "era_symbol": None,
            "region_affinity": None,
            "supporting_evidence": hypothesis["supporting_evidence"],
            "counterevidence": hypothesis["counterevidence"],
            "strength": hypothesis["strength"],
            "confidence": "research_only",
            "status": "research_preview",
        }
        for hypothesis in ranked[:3]
    ]
    locked = {
        "verdict": status,
        "status": "research_preview",
        "ranked_hypotheses": ranked,
        "past_life_nodes": nodes,
        "ruleset_version": config["version"],
        "claim_snapshot": case.get("claim_snapshot", []),
        "random_seed": case["random_seed"],
    }
    return {
        "input_hash": legacy_stable_hash(case),
        "signals": signals,
        "weights": weights,
        "locked_verdict": locked,
        "locked_hash": legacy_stable_hash(locked),
        "stages": list(LEGACY_STAGES),
        "research_trace": {
            "deduplication": deduplication,
            "candidate_generation": candidate_generation,
            "candidate_contributions": [
                {
                    "candidate_id": item["id"],
                    "supporting_evidence": item["supporting_evidence"],
                    "counterevidence": item["counterevidence"],
                    "hard_conflicts": item["hard_conflicts"],
                    "contributions": item["contributions"],
                    "raw_score": item["raw_score"],
                    "strength": item["strength"],
                    "sort_key": [item["raw_score"], item["id"]],
                    "rank": item.get("rank"),
                }
                for item in scored
            ],
            "status_decision": status_reason,
            "method_version": "INFERENCE.RESEARCH_BASELINE.0.1.0",
            "ruleset_version": config["version"],
        },
    }
