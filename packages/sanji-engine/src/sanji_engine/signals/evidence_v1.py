"""User-authorized evidence adapter for Liuxiang research v1.

This module consumes normalized facts, never private narrative text. Coverage
and structural facts can affect completeness and confidence but always carry a
zero magnitude. Only explicit user evidence governed by the versioned policy
can contribute to strength.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from importlib.resources import files

from .. import __version__
from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID
from ..inference.liuxiang_v1 import (
    load_liuxiang_assets,
    run_liuxiang_from_signals,
)

OPERATION = "run_liuxiang_evidence_v1"
METHOD_ID = "INFERENCE.LIUXIANG.USER_EVIDENCE.RESEARCH.V1"
SIGNAL_METHOD_ID = "SIGNALS.V2.LIUXIANG.USER_EVIDENCE.RESEARCH.V1"
POLICY_FILE = "liuxiang-evidence-policies-1.0.0.json"
MAPPING_FILE = "liuxiang-evidence-mappings-1.0.0.json"
INFERENCE_FILE = "liuxiang-evidence-inference-policy-1.0.0.json"

ALLOWED_FACT_KINDS = {"coverage", "structural", "evidence"}
ALLOWED_PRECISIONS = {"exact_date", "month_only", "year_only", "unknown"}
ALLOWED_DIRECTIONS = {"positive", "negative", "neutral"}


def _load_asset(name: str) -> dict:
    value = json.loads(
        files("sanji_engine").joinpath(f"rulesets/assets/{name}").read_text(encoding="utf-8")
    )
    expected = value.get("content_hash")
    actual = content_hash({key: item for key, item in value.items() if key != "content_hash"})
    if expected != actual:
        raise EngineError(INPUT_INVALID, f"Liuxiang evidence asset hash mismatch: {name}")
    for item in value.get("policies", []) + value.get("rules", []):
        item_expected = item.get("content_hash")
        item_actual = content_hash({
            key: child for key, child in item.items() if key != "content_hash"
        })
        if item_expected != item_actual:
            raise EngineError(INPUT_INVALID, f"Liuxiang evidence item hash mismatch: {name}")
    return value


def load_liuxiang_evidence_assets() -> tuple[dict, dict, dict, dict]:
    dimensions, _, _ = load_liuxiang_assets()
    return (
        dimensions,
        _load_asset(MAPPING_FILE),
        _load_asset(INFERENCE_FILE),
        _load_asset(POLICY_FILE),
    )


def _bp(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10_000:
        raise EngineError(INPUT_INVALID, f"{path} must be an integer basis-point value")
    return value


def _round_ratio(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient % 2):
        quotient += 1
    return quotient


def _parse_exact_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _validate_fact(value: object, dimensions: set[str]) -> dict:
    if not isinstance(value, dict):
        raise EngineError(INPUT_INVALID, "Evidence fact must be an object")
    allowed = {
        "record_id", "dimension_id", "fact_kind", "occurred_on", "date_precision",
        "state", "direction", "source_reliability_bp", "confirmed_tags",
        "coverage_fields", "shared_source_group", "profile_id", "withdrawn",
        "counterevidence", "conflicts", "relationship_confirmation",
        "consent_active", "profile_dispute_bp", "boundary_sensitivity_bp",
        "source_type", "verification_status",
    }
    unexpected = sorted(value.keys() - allowed)
    if unexpected:
        raise EngineError(INPUT_INVALID, "Evidence fact has unexpected fields", {
            "fields": unexpected,
        })
    fact = deepcopy(value)
    for field in ("record_id", "dimension_id", "fact_kind"):
        if not isinstance(fact.get(field), str) or not fact[field]:
            raise EngineError(INPUT_INVALID, f"Evidence fact {field} is required")
    if fact["dimension_id"] not in dimensions:
        raise EngineError(INPUT_INVALID, "Evidence fact dimension is unknown")
    if fact["fact_kind"] not in ALLOWED_FACT_KINDS:
        raise EngineError(
            INPUT_INVALID,
            "Interpretive or unknown facts are disabled for user evidence execution",
        )
    fact["date_precision"] = fact.get("date_precision", "unknown")
    if fact["date_precision"] not in ALLOWED_PRECISIONS:
        raise EngineError(INPUT_INVALID, "Evidence date precision is invalid")
    fact["direction"] = fact.get("direction", "positive")
    if fact["direction"] not in ALLOWED_DIRECTIONS:
        raise EngineError(INPUT_INVALID, "Evidence direction is invalid")
    fact["source_reliability_bp"] = _bp(
        fact.get("source_reliability_bp", 7000), "source_reliability_bp"
    )
    fact["profile_dispute_bp"] = _bp(
        fact.get("profile_dispute_bp", 0), "profile_dispute_bp"
    )
    fact["boundary_sensitivity_bp"] = _bp(
        fact.get("boundary_sensitivity_bp", 0), "boundary_sensitivity_bp"
    )
    for field in ("confirmed_tags", "counterevidence", "conflicts"):
        raw = fact.get(field, [])
        if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
            raise EngineError(INPUT_INVALID, f"Evidence fact {field} must be a string array")
        fact[field] = sorted(set(raw))
    coverage = fact.get("coverage_fields", {})
    if not isinstance(coverage, dict) or any(
        not isinstance(key, str) or not isinstance(flag, bool)
        for key, flag in coverage.items()
    ):
        raise EngineError(INPUT_INVALID, "coverage_fields must be a boolean object")
    fact["coverage_fields"] = dict(sorted(coverage.items()))
    fact["withdrawn"] = bool(fact.get("withdrawn", False))
    fact["consent_active"] = bool(fact.get("consent_active", True))
    fact["state"] = str(fact.get("state", "observed"))
    # The default group is the original record itself. Callers must explicitly
    # provide a common group when multiple descriptions refer to one event.
    fact["shared_source_group"] = str(
        fact.get("shared_source_group") or f"record:{fact['record_id']}"
    )
    fact["profile_id"] = (
        str(fact["profile_id"]) if fact.get("profile_id") is not None else None
    )
    fact["relationship_confirmation"] = str(
        fact.get("relationship_confirmation", "not_applicable")
    )
    fact["source_type"] = str(fact.get("source_type", "user_record"))
    fact["verification_status"] = str(
        fact.get("verification_status", "user_self_report")
    )
    occurred = fact.get("occurred_on")
    if occurred is not None and not isinstance(occurred, str):
        raise EngineError(INPUT_INVALID, "occurred_on must be a precision-preserving string")
    if fact["date_precision"] == "exact_date" and _parse_exact_date(occurred) is None:
        raise EngineError(INPUT_INVALID, "exact_date evidence requires YYYY-MM-DD")
    if fact["date_precision"] == "year_only" and (
        not isinstance(occurred, str) or len(occurred) != 4 or not occurred.isdigit()
    ):
        raise EngineError(INPUT_INVALID, "year_only evidence must remain YYYY")
    if fact["date_precision"] == "month_only" and (
        not isinstance(occurred, str)
        or len(occurred) != 7
        or occurred[4] != "-"
        or not (occurred[:4] + occurred[5:]).isdigit()
        or not 1 <= int(occurred[5:]) <= 12
    ):
        raise EngineError(INPUT_INVALID, "month_only evidence must remain YYYY-MM")
    return fact


def _deduplicate_facts(facts: list[dict]) -> tuple[list[dict], list[dict]]:
    selected: dict[str, dict] = {}
    decisions: list[dict] = []
    for fact in sorted(facts, key=lambda item: (
        item["dimension_id"], item["record_id"], content_hash(item)
    )):
        key = f"{fact['dimension_id']}:{fact['record_id']}"
        retained = key not in selected
        if retained:
            selected[key] = fact
        decisions.append({
            "record_id": fact["record_id"],
            "dimension_id": fact["dimension_id"],
            "record_fingerprint": content_hash({
                "dimension_id": fact["dimension_id"],
                "record_id": fact["record_id"],
            }),
            "retained": retained,
            "reason": "unique_source_record" if retained else "duplicate_source_record",
        })
    return list(selected.values()), decisions


def _coverage(
    policy: dict,
    facts: list[dict],
) -> tuple[int, list[str], int]:
    required = policy["required_coverage_fields"]
    if required:
        fields: dict[str, bool] = {}
        for fact in facts:
            for key, present in fact["coverage_fields"].items():
                fields[key] = fields.get(key, False) or present
        present = sum(1 for key in required if fields.get(key, False))
        completeness = _round_ratio(present * 10_000, len(required))
        missing = sorted(key for key in required if not fields.get(key, False))
        return completeness, missing, 0
    active = [fact for fact in facts if fact["fact_kind"] == "evidence"]
    target = max(1, policy["coverage_target_records"])
    count_bp = min(10_000, _round_ratio(len(active) * 10_000, target))
    exact_dates = sorted({
        parsed for fact in active
        if fact["date_precision"] == "exact_date"
        if (parsed := _parse_exact_date(fact.get("occurred_on"))) is not None
    })
    span_days = (exact_dates[-1] - exact_dates[0]).days if len(exact_dates) >= 2 else 0
    required_span = policy["minimum_time_span_days"]
    span_bp = (
        10_000 if required_span == 0
        else min(10_000, _round_ratio(span_days * 10_000, required_span))
    )
    completeness = _round_ratio(count_bp + span_bp, 2)
    missing = []
    if len(active) < policy["minimum_independent_records"]:
        missing.append("minimum_independent_records")
    if span_days < required_span:
        missing.append("minimum_time_span")
    return completeness, missing, span_days


def _signal(
    fact: dict,
    policy: dict,
    *,
    magnitude_bp: int,
    direction: str,
    missing_facts: list[str],
    mapping_reliability_bp: int,
    suffix: str = "evidence",
) -> dict:
    dimension = fact["dimension_id"]
    supports = [dimension] if direction == "positive" and magnitude_bp else []
    counter = [dimension] if direction == "negative" and magnitude_bp else []
    source_reliability = min(
        fact["source_reliability_bp"], policy["source_reliability_cap_bp"]
    )
    if dimension == "lx_yuan_relation":
        confirmation = fact["relationship_confirmation"]
        if confirmation == "single_party":
            mapping_reliability_bp = _round_ratio(mapping_reliability_bp * 5000, 10_000)
        elif confirmation == "mutual" and fact["consent_active"]:
            mapping_reliability_bp = min(10_000, mapping_reliability_bp)
        elif not fact["consent_active"]:
            magnitude_bp = 0
            direction = "neutral"
            supports = []
            counter = []
    base = {
        "schema_version": "signal-v2/1.0.0",
        "signal_id": f"signal:{dimension}:{fact['record_id']}:{suffix}",
        "subject_id": str(fact.get("profile_id") or "subject"),
        "dimension_id": dimension,
        "direction": direction,
        "magnitude_bp": magnitude_bp,
        "source_system": "user_evidence",
        "source_record_id": fact["record_id"],
        "source_fact_path": f"$.records[{fact['record_id']}]",
        "source_claim_ids": ["SANJI_USER_CONFIRMED_RECORD"],
        "source_dataset_id": None,
        "source_dataset_revision": None,
        "mapping_rule_id": policy["mapping_rule_id"],
        "mapping_ruleset_version": policy["ruleset_version"],
        "profile_id": fact.get("profile_id"),
        "source_reliability_bp": source_reliability,
        "mapping_reliability_bp": mapping_reliability_bp,
        "independence_group": f"record:{fact['record_id']}",
        "shared_source_group": fact["shared_source_group"],
        "temporal_scope": {
            "occurred_on": fact.get("occurred_on"),
            "date_precision": fact["date_precision"],
        },
        "supports": supports,
        "counterevidence": counter + fact["counterevidence"],
        "missingness": {
            "facts": missing_facts,
            "penalty_bp": 0,
        },
        "disputes": {
            "hard_conflicts": [],
            "soft_conflicts": fact["conflicts"],
            "penalty_bp": fact["profile_dispute_bp"],
        },
        "boundary_sensitivity": {
            "penalty_bp": fact["boundary_sensitivity_bp"],
        },
        "trace_ref": f"evidence:{fact['record_id']}",
        "engine_version": __version__,
    }
    base["content_hash"] = content_hash(base)
    return base


def adapt_user_evidence(snapshot: dict) -> tuple[list[dict], dict[str, int], list[dict], dict]:
    dimensions_asset, _, _, policy_asset = load_liuxiang_evidence_assets()
    dimension_ids = {item["dimension_id"] for item in dimensions_asset["dimensions"]}
    raw = snapshot.get("facts", [])
    if not isinstance(raw, list):
        raise EngineError(INPUT_INVALID, "facts must be an array")
    facts = [_validate_fact(item, dimension_ids) for item in raw]
    excluded = snapshot.get("excluded_record_ids", [])
    if not isinstance(excluded, list) or any(not isinstance(item, str) for item in excluded):
        raise EngineError(INPUT_INVALID, "excluded_record_ids must be a string array")
    excluded_set = set(excluded)
    active = [
        fact for fact in facts
        if not fact["withdrawn"] and fact["record_id"] not in excluded_set
    ]
    unique, duplicate_decisions = _deduplicate_facts(active)
    policies = {item["dimension_id"]: item for item in policy_asset["policies"]}
    signals: list[dict] = []
    completeness: dict[str, int] = {}
    policy_decisions: list[dict] = []
    for dimension in sorted(dimension_ids):
        policy = policies[dimension]
        channel_facts = [
            fact for fact in unique if fact["dimension_id"] == dimension
        ]
        raw_evidence_facts = sorted(
            [fact for fact in channel_facts if fact["fact_kind"] == "evidence"],
            key=lambda fact: (
                fact.get("occurred_on") or "9999",
                fact["record_id"],
                content_hash(fact),
            ),
        )
        evidence_facts: list[dict] = []
        shared_duplicate_facts: list[dict] = []
        seen_shared_groups: set[str] = set()
        for fact in raw_evidence_facts:
            if fact["shared_source_group"] in seen_shared_groups:
                shared_duplicate_facts.append(fact)
            else:
                seen_shared_groups.add(fact["shared_source_group"])
                evidence_facts.append(fact)
        policy_channel_facts = [
            fact for fact in channel_facts if fact["fact_kind"] != "evidence"
        ] + evidence_facts
        channel_complete, missing, span_days = _coverage(policy, policy_channel_facts)
        completeness[dimension] = channel_complete
        coverage_fact = {
            "record_id": f"coverage:{dimension}",
            "dimension_id": dimension,
            "fact_kind": "coverage",
            "occurred_on": None,
            "date_precision": "unknown",
            "state": "coverage",
            "direction": "neutral",
            "source_reliability_bp": 10_000,
            "confirmed_tags": [],
            "coverage_fields": {},
            "shared_source_group": "profile_coverage",
            "profile_id": str(snapshot.get("subject_id", "subject")),
            "withdrawn": False,
            "counterevidence": [],
            "conflicts": [],
            "relationship_confirmation": "not_applicable",
            "consent_active": True,
            "profile_dispute_bp": max(
                (fact["profile_dispute_bp"] for fact in channel_facts), default=0
            ),
            "boundary_sensitivity_bp": max(
                (fact["boundary_sensitivity_bp"] for fact in channel_facts), default=0
            ),
            "source_type": "coverage",
            "verification_status": "derived_coverage_only",
        }
        coverage_signal = _signal(
            coverage_fact,
            policy,
            magnitude_bp=0,
            direction="neutral",
            missing_facts=missing,
            mapping_reliability_bp=10_000,
            suffix="coverage",
        )
        coverage_signal["missingness"]["penalty_bp"] = 10_000 - channel_complete
        coverage_signal["content_hash"] = content_hash({
            key: value for key, value in coverage_signal.items() if key != "content_hash"
        })
        signals.append(coverage_signal)
        # Preserve each authorized coverage/structural record in Signal v2 and
        # Trace while keeping its magnitude at zero. Mechanical structure is
        # not silently converted into a life interpretation.
        for fact in sorted(
            [item for item in channel_facts if item["fact_kind"] != "evidence"],
            key=lambda item: (item["fact_kind"], item["record_id"], content_hash(item)),
        ):
            signals.append(_signal(
                fact,
                policy,
                magnitude_bp=0,
                direction="neutral",
                missing_facts=[],
                mapping_reliability_bp=0,
                suffix=fact["fact_kind"],
            ))
        for fact in shared_duplicate_facts:
            signals.append(_signal(
                fact,
                policy,
                magnitude_bp=0,
                direction="neutral",
                missing_facts=[],
                mapping_reliability_bp=policy["mapping_reliability_bp"],
                suffix="shared-source-duplicate",
            ))
            policy_decisions.append({
                "record_id": fact["record_id"],
                "dimension_id": dimension,
                "eligible": False,
                "same_day_capped": False,
                "contribution_bp": 0,
                "reason": "shared_source_duplicate",
            })
        minimum_met = (
            len(evidence_facts) >= policy["minimum_independent_records"]
            and span_days >= policy["minimum_time_span_days"]
        )
        used_dates: set[str] = set()
        group_total = 0
        contribution_index = 0
        for fact in evidence_facts:
            same_day_blocked = (
                fact["date_precision"] == "exact_date"
                and fact.get("occurred_on") in used_dates
                and policy["same_day_record_cap"] == 1
            )
            eligible = minimum_met and not same_day_blocked
            if dimension == "lx_yuan" and len(evidence_facts) == 1:
                eligible = True
            if dimension == "lx_meng" and not fact["confirmed_tags"]:
                eligible = False
            if dimension == "lx_yuan_relation" and not fact["consent_active"]:
                eligible = False
            contribution = 0
            if eligible:
                table = policy["diminishing_returns_bp"]
                contribution = table[min(contribution_index, len(table) - 1)]
                state_multiplier = policy["state_multipliers_bp"].get(
                    fact["state"], policy["state_multipliers_bp"]["default"]
                )
                contribution = _round_ratio(contribution * state_multiplier, 10_000)
                contribution = min(contribution, policy["single_event_cap_bp"])
                contribution = min(
                    contribution,
                    max(0, policy["independence_group_cap_bp"] - group_total),
                )
                group_total += contribution
                contribution_index += 1
                if fact["date_precision"] == "exact_date" and fact.get("occurred_on"):
                    used_dates.add(fact["occurred_on"])
            direction = fact["direction"] if contribution else "neutral"
            signals.append(_signal(
                fact,
                policy,
                magnitude_bp=contribution,
                direction=direction,
                missing_facts=[],
                mapping_reliability_bp=policy["mapping_reliability_bp"],
            ))
            policy_decisions.append({
                "record_id": fact["record_id"],
                "dimension_id": dimension,
                "eligible": eligible,
                "same_day_capped": same_day_blocked,
                "contribution_bp": contribution,
                "reason": (
                    "policy_eligible"
                    if eligible else "minimum_span_count_tags_or_consent_not_met"
                ),
            })
    metadata = {
        "policy_id": policy_asset["policy_id"],
        "policy_version": policy_asset["version"],
        "policy_hash": policy_asset["content_hash"],
        "selected_record_ids": sorted({
            fact["record_id"] for fact in unique if fact["fact_kind"] == "evidence"
        }),
        "excluded_record_ids": sorted(excluded_set),
        "withdrawn_record_ids": sorted({
            fact["record_id"] for fact in facts if fact["withdrawn"]
        }),
        "fact_deduplication": duplicate_decisions,
        "policy_decisions": policy_decisions,
    }
    return signals, completeness, policy_decisions, metadata


def run_liuxiang_evidence_v1(snapshot: dict) -> tuple[dict, list[dict]]:
    if snapshot.get("operation") != OPERATION:
        raise EngineError(INPUT_INVALID, "Liuxiang user-evidence operation is unsupported")
    dimensions, mappings, inference_policy, evidence_policy = load_liuxiang_evidence_assets()
    signals, completeness, decisions, metadata = adapt_user_evidence(snapshot)
    inference_snapshot = {
        "operation": OPERATION,
        "subject_id": str(snapshot.get("subject_id", "subject")),
        "signals": signals,
        "completeness_bp_by_dimension": completeness,
    }
    result, trace = run_liuxiang_from_signals(
        inference_snapshot,
        dimensions_asset=dimensions,
        mappings_asset=mappings,
        policy=inference_policy,
        expected_operation=OPERATION,
        method_id=METHOD_ID,
        signal_method_id=SIGNAL_METHOD_ID,
        result_metadata={
            "evidence_policy_id": evidence_policy["policy_id"],
            "evidence_policy_version": evidence_policy["version"],
            "evidence_policy_hash": evidence_policy["content_hash"],
            "evidence_selection": metadata,
            "coverage_bp_by_dimension": completeness,
        },
    )
    adapter_step = {
        "step_id": "signals:050:adapt_user_evidence",
        "sequence": 50,
        "module_id": "signals",
        "operation": "adapt_user_evidence",
        "input_refs": ["input:facts", "input:excluded_record_ids"],
        "rule_refs": [evidence_policy["policy_id"]],
        "source_refs": ["SANJI_USER_AUTHORIZED_PRIVATE_RECORDS"],
        "parameters": {
            "policy_hash": evidence_policy["content_hash"],
            "decision_count": len(decisions),
            "selected_record_ids": metadata["selected_record_ids"],
            "excluded_record_ids": metadata["excluded_record_ids"],
            "withdrawn_record_ids": metadata["withdrawn_record_ids"],
        },
        "output_refs": ["signals:user-evidence-v2"],
    }
    adapter_step["calculation_hash"] = content_hash(adapter_step)
    return result, [adapter_step, *trace]
