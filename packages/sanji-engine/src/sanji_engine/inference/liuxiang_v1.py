"""Deterministic Sanji-original Liuxiang research inference v1."""
from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files

from .. import __version__
from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID
from ..signals.v2 import deduplicate_signals_v2, validate_signals_v2

METHOD_ID = "INFERENCE.LIUXIANG.RESEARCH.V1"
SIGNAL_METHOD_ID = "SIGNALS.V2.LIUXIANG.RESEARCH.V1"


def _load(name: str) -> dict:
    return json.loads(
        files("sanji_engine").joinpath(f"rulesets/assets/{name}").read_text(encoding="utf-8")
    )


def load_liuxiang_assets() -> tuple[dict, dict, dict]:
    dimensions = _load("liuxiang-dimensions-1.0.0.json")
    mappings = _load("liuxiang-mappings-1.0.0.json")
    policy = _load("liuxiang-inference-policy-1.0.0.json")
    for value in (dimensions, mappings, policy):
        expected = value["content_hash"]
        actual = content_hash({k: v for k, v in value.items() if k != "content_hash"})
        if expected != actual:
            raise EngineError(INPUT_INVALID, "Liuxiang asset content hash mismatch")
    for item in [*dimensions["dimensions"], *mappings["rules"]]:
        if item["content_hash"] != content_hash({
            key: value for key, value in item.items() if key != "content_hash"
        }):
            raise EngineError(INPUT_INVALID, "Liuxiang dimension or mapping hash mismatch")
    return dimensions, mappings, policy


def _round_ratio(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient % 2):
        quotient += 1
    return quotient


def _weighted(values: list[tuple[int, int]]) -> int:
    denominator = sum(weight for _, weight in values)
    return _round_ratio(sum(value * weight for value, weight in values), denominator)


def _effective(signal: dict) -> int:
    return _round_ratio(
        signal["magnitude_bp"]
        * signal["source_reliability_bp"]
        * signal["mapping_reliability_bp"],
        100_000_000,
    )


def _flag_bp(value: object, default: int = 0) -> int:
    if isinstance(value, dict):
        value = value.get("penalty_bp", default)
    if isinstance(value, bool):
        return 10_000 if value else 0
    return value if isinstance(value, int) and 0 <= value <= 10_000 else default


def _shared_source_cap(signals: list[dict]) -> tuple[list[dict], list[dict]]:
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for signal in signals:
        key = (
            signal["dimension_id"],
            signal["direction"],
            signal["shared_source_group"],
        )
        groups.setdefault(key, []).append(signal)
    retained: list[dict] = []
    decisions: list[dict] = []
    for key in sorted(groups):
        members = sorted(
            groups[key],
            key=lambda value: (-_effective(value), value["signal_id"]),
        )
        winner = members[0]
        retained.append(winner)
        for member in members:
            decisions.append({
                "signal_id": member["signal_id"],
                "shared_source_group": key[2],
                "retained_for_strength": member["signal_id"] == winner["signal_id"],
                "retained_for_independence": member["signal_id"] == winner["signal_id"],
                "policy": "strongest_per_dimension_direction_shared_source",
            })
    return sorted(retained, key=lambda value: (value["dimension_id"], value["signal_id"])), decisions


def _candidate(
    dimension: dict,
    signals: list[dict],
    completeness_bp: int,
    policy: dict,
) -> dict:
    supporting = [value for value in signals if value["direction"] == "positive"]
    opposing = [value for value in signals if value["direction"] == "negative"]
    neutral = [value for value in signals if value["direction"] == "neutral"]
    support_bp = min(10_000, sum(_effective(value) for value in supporting))
    counter_bp = min(10_000, sum(_effective(value) for value in opposing))
    strength_bp = max(0, support_bp - counter_bp)
    all_directional = supporting + opposing
    reliability_bp = (
        _weighted([
            (
                _round_ratio(
                    value["source_reliability_bp"] * value["mapping_reliability_bp"],
                    10_000,
                ),
                max(1, value["magnitude_bp"]),
            )
            for value in all_directional
        ])
        if all_directional else 0
    )
    independent_groups = sorted({
        value["independence_group"] for value in all_directional
    })
    independent_count = len(independent_groups)
    independence_bp = min(10_000, independent_count * policy["independence_step_bp"])
    profile_penalty = max((_flag_bp(value["disputes"]) for value in signals), default=0)
    boundary_penalty = max(
        (_flag_bp(value["boundary_sensitivity"]) for value in signals), default=0
    )
    missing_penalty = max((_flag_bp(value["missingness"]) for value in signals), default=0)
    conflict_penalty = min(
        10_000,
        _round_ratio(min(support_bp, counter_bp) * policy["conflict_penalty_multiplier_bp"], 10_000),
    )
    confidence_base = _weighted([
        (reliability_bp, policy["confidence_weights"]["reliability"]),
        (independence_bp, policy["confidence_weights"]["independence"]),
        (completeness_bp, policy["confidence_weights"]["completeness"]),
        (10_000 - profile_penalty, policy["confidence_weights"]["profile_consistency"]),
        (10_000 - boundary_penalty, policy["confidence_weights"]["boundary_stability"]),
        (10_000 - missing_penalty, policy["confidence_weights"]["data_quality"]),
    ])
    confidence_bp = max(0, confidence_base - conflict_penalty)
    hard_conflicts = sorted({
        conflict
        for value in signals
        for conflict in value["disputes"].get("hard_conflicts", [])
        if isinstance(conflict, str)
    })
    soft_conflicts = sorted({
        conflict
        for value in signals
        for conflict in value["disputes"].get("soft_conflicts", [])
        if isinstance(conflict, str)
    })
    missing_facts = sorted({
        fact
        for value in signals
        for fact in value["missingness"].get("facts", [])
        if isinstance(fact, str)
    })
    base = {
        "candidate_id": f"candidate:{dimension['dimension_id']}",
        "dimension_id": dimension["dimension_id"],
        "supporting_signal_ids": [value["signal_id"] for value in supporting],
        "counterevidence_signal_ids": [value["signal_id"] for value in opposing],
        "neutral_signal_ids": [value["signal_id"] for value in neutral],
        "hard_conflicts": hard_conflicts,
        "soft_conflicts": soft_conflicts,
        "missing_facts": missing_facts,
        "source_coverage": {
            "completeness_bp": completeness_bp,
            "source_systems": sorted({value["source_system"] for value in signals}),
        },
        "independent_evidence_count": independent_count,
        "independence_groups": independent_groups,
        "shared_source_groups": sorted({value["shared_source_group"] for value in signals}),
        "raw_strength": {"support_bp": support_bp, "counterevidence_bp": counter_bp},
        "calibrated_strength_bp": strength_bp,
        "confidence_bp": confidence_bp,
        "status": "pending",
        "rank": 0,
        "stable_tie_break_key": dimension["stable_order_key"],
        "ruleset_version": policy["ruleset_version"],
        "trace_ref": f"candidate:{dimension['dimension_id']}",
    }
    return {**base, "result_hash": content_hash(base)}


def run_liuxiang_research_v1(snapshot: dict) -> tuple[dict, list[dict]]:
    dimensions_asset, mappings_asset, policy = load_liuxiang_assets()
    if snapshot.get("operation") != "run_liuxiang_research_v1":
        raise EngineError(INPUT_INVALID, "Liuxiang research operation is unsupported")
    dimensions = dimensions_asset["dimensions"]
    dimension_ids = {value["dimension_id"] for value in dimensions}
    raw_signals = validate_signals_v2(snapshot.get("signals", []), dimension_ids)
    active_mapping_ids = {
        value["mapping_rule_id"]
        for value in mappings_asset["rules"]
        if value["activation_status"] == "research_active"
    }
    for signal in raw_signals:
        if signal["mapping_rule_id"] not in active_mapping_ids:
            raise EngineError(INPUT_INVALID, "Signal references a mapping rule that is not research_active")
        if (
            signal["mapping_rule_id"] == "LX.SYNTHETIC.CONFORMANCE.V1"
            and signal["source_system"] != "synthetic_conformance"
        ):
            raise EngineError(INPUT_INVALID, "synthetic conformance mapping cannot accept real source systems")
    deduplicated, exact_decisions = deduplicate_signals_v2(raw_signals)
    capped, shared_decisions = _shared_source_cap(deduplicated)
    completeness = snapshot.get("completeness_bp_by_dimension", {})
    if not isinstance(completeness, dict):
        raise EngineError(INPUT_INVALID, "completeness_bp_by_dimension must be an object")
    candidates: list[dict] = []
    for dimension in dimensions:
        value = completeness.get(dimension["dimension_id"], 0)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10_000:
            raise EngineError(INPUT_INVALID, "dimension completeness must be integer basis points")
        candidates.append(_candidate(
            dimension,
            [signal for signal in capped if signal["dimension_id"] == dimension["dimension_id"]],
            value,
            policy,
        ))
    candidates.sort(key=lambda value: (
        -value["calibrated_strength_bp"],
        -value["confidence_bp"],
        value["stable_tie_break_key"],
        value["candidate_id"],
    ))
    for rank, candidate in enumerate(candidates, 1):
        candidate["rank"] = rank
    top = candidates[0]
    second = candidates[1]
    gap = top["calibrated_strength_bp"] - second["calibrated_strength_bp"]
    thresholds = policy["status_thresholds"]
    if (
        top["source_coverage"]["completeness_bp"] < thresholds["minimum_completeness_bp"]
        or top["independent_evidence_count"] == 0
    ):
        overall_status = "insufficient"
    elif top["hard_conflicts"] or (
        gap <= thresholds["contested_gap_bp"]
        and second["calibrated_strength_bp"] >= thresholds["contested_second_strength_bp"]
    ):
        overall_status = "contested"
    elif (
        top["calibrated_strength_bp"] >= thresholds["decisive_strength_bp"]
        and top["confidence_bp"] >= thresholds["decisive_confidence_bp"]
        and top["independent_evidence_count"] >= thresholds["decisive_independent_count"]
        and gap >= thresholds["decisive_gap_bp"]
    ):
        overall_status = "decisive"
    elif top["calibrated_strength_bp"] > 0:
        overall_status = "provisional"
    else:
        overall_status = "insufficient"
    for candidate in candidates:
        candidate["status"] = overall_status if candidate is top else "provisional"
        candidate["result_hash"] = content_hash({
            key: value for key, value in candidate.items() if key != "result_hash"
        })
    trace = [
        {
            "step_id": "signals:100:validate_signal_v2",
            "sequence": 100,
            "module_id": "signals",
            "operation": "validate_signal_v2",
            "input_refs": ["input:signals"],
            "rule_refs": [SIGNAL_METHOD_ID],
            "source_refs": ["SANJI_ORIGINAL_RESEARCH"],
            "parameters": {"count": len(raw_signals)},
            "output_refs": ["signals:validated"],
        },
        {
            "step_id": "signals:200:deduplicate_sources",
            "sequence": 200,
            "module_id": "signals",
            "operation": "deduplicate_sources",
            "input_refs": ["signals:validated"],
            "rule_refs": [policy["ruleset_version"]],
            "source_refs": ["SANJI_ORIGINAL_RESEARCH"],
            "parameters": {
                "exact_decisions": exact_decisions,
                "shared_source_decisions": shared_decisions,
            },
            "output_refs": ["signals:effective"],
        },
        {
            "step_id": "inference:300:score_strength_confidence",
            "sequence": 300,
            "module_id": "inference",
            "operation": "score_strength_confidence",
            "input_refs": ["signals:effective"],
            "rule_refs": [METHOD_ID, policy["ruleset_version"]],
            "source_refs": ["SANJI_ORIGINAL_RESEARCH"],
            "parameters": {
                "integer_policy": "basis_points_round_half_even",
                "candidate_order": [value["candidate_id"] for value in candidates],
            },
            "output_refs": ["inference:candidates"],
        },
        {
            "step_id": "inference:400:decide_status",
            "sequence": 400,
            "module_id": "inference",
            "operation": "decide_status",
            "input_refs": ["inference:candidates"],
            "rule_refs": [policy["ruleset_version"]],
            "source_refs": ["SANJI_ORIGINAL_RESEARCH"],
            "parameters": {
                "status": overall_status,
                "top_gap_bp": gap,
                "thresholds": thresholds,
            },
            "output_refs": ["inference:result"],
        },
    ]
    for step in trace:
        step["calculation_hash"] = content_hash(step)
    result_base = {
        "schema_version": "liuxiang-result/1.0.0",
        "tradition_scope": "sanji_original",
        "activation": "research_active",
        "review_status": "UNCONFIRMED",
        "production_activatable": False,
        "engine_version": __version__,
        "ruleset_version": policy["ruleset_version"],
        "dimension_contract_hash": dimensions_asset["content_hash"],
        "mapping_asset_hash": mappings_asset["content_hash"],
        "signals": raw_signals,
        "effective_signals": capped,
        "deduplication": exact_decisions,
        "shared_source_discounts": shared_decisions,
        "candidates": candidates,
        "status": overall_status,
        "leading_candidate_id": top["candidate_id"],
        "strength_bp": top["calibrated_strength_bp"],
        "confidence_bp": top["confidence_bp"],
        "trace_ref": "trace:liuxiang-v1",
    }
    return {**result_base, "result_hash": content_hash(result_base)}, trace
