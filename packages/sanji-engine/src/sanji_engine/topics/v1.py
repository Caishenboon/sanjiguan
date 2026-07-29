"""Shared deterministic evidence-graph engine for three research topics.

This is a Sanji-original, unconfirmed research model.  It does not assert
historical identity, metaphysical fact, future death, or immutable relationship
outcomes.  Every non-observed field carries an explicit epistemic status.
"""
from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files

from .. import __version__
from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID

OPERATION = "run_topic_research_v1"
SIGNAL_METHOD_ID = "SIGNALS.TOPIC.EVIDENCE_GRAPH.RESEARCH.V1"
INFERENCE_METHOD_ID = "INFERENCE.TOPIC.SANJI_ORIGINAL.RESEARCH.V1"
RULESET_VERSION = "topic-research-rules/1.0.0"
NAME_RULESET_VERSION = "past-life-name-rules/1.0.0"
TOPICS = {"sushe", "zhongyin_life", "zhongyin_deceased", "yuanqi"}
NODE_TYPES = {
    "subject", "relationship", "life_event", "behavior_pattern", "vow",
    "dream_tag", "mechanical_chart_reference", "time_window",
    "transition_episode", "topic_candidate", "identity_candidate",
    "debt_candidate", "evidence_group", "missing_fact", "conflict",
}
EDGE_TYPES = {
    "supports", "counters", "conflicts_with", "derived_from", "repeats",
    "continues", "interrupts", "precedes", "follows", "involves",
    "corresponds_to", "confirmed_by", "revoked_by", "owed_to", "repays",
    "unfulfilled_from",
}
FORBIDDEN_TEXT_FIELDS = {
    "text", "free_text", "dream_text", "journal_text", "relationship_text",
    "narrative", "provider_prompt", "llm_output", "oracle_output",
}


def _load(name: str) -> dict:
    return json.loads(
        files("sanji_engine").joinpath(f"rulesets/assets/{name}").read_text(encoding="utf-8")
    )


def load_topic_assets() -> tuple[dict, dict]:
    rules = _load("topic-research-rules-1.0.0.json")
    names = _load("past-life-name-rules-1.0.0.json")
    for asset in (rules, names):
        expected = asset["content_hash"]
        actual = content_hash({k: v for k, v in asset.items() if k != "content_hash"})
        if expected != actual:
            raise EngineError(INPUT_INVALID, "topic research asset content hash mismatch")
    return rules, names


def _hash_index(seed: object, size: int, salt: str = "") -> int:
    digest = content_hash({"seed": seed, "salt": salt}).split(":", 1)[1]
    return int(digest[:16], 16) % size


def _pick(values: list, seed: object, salt: str) -> object:
    return deepcopy(values[_hash_index(seed, len(values), salt)])


def _ep(value: object, status: str, confidence_bp: int) -> dict:
    return {
        "value": value,
        "epistemic_status": status,
        "confidence_bp": max(0, min(10_000, confidence_bp)),
    }


def _stable_id(prefix: str, value: object) -> str:
    return f"{prefix}_{content_hash(value).split(':', 1)[1][:24]}"


def _normalize_fact(fact: dict) -> dict:
    if not isinstance(fact, dict):
        raise EngineError(INPUT_INVALID, "topic fact must be an object")
    forbidden = sorted(FORBIDDEN_TEXT_FIELDS & set(fact))
    if forbidden:
        raise EngineError(
            INPUT_INVALID,
            "private narrative is forbidden in the topic graph",
            {"fields": forbidden},
        )
    if fact.get("node_type") not in NODE_TYPES - {
        "topic_candidate", "identity_candidate", "debt_candidate",
        "evidence_group", "missing_fact", "conflict",
    }:
        raise EngineError(INPUT_INVALID, "topic fact node_type is not supported")
    record_id = fact.get("record_id")
    if not isinstance(record_id, str) or not record_id:
        raise EngineError(INPUT_INVALID, "topic fact requires record_id")
    tags = fact.get("tags", [])
    if not isinstance(tags, list) or any(not isinstance(item, str) for item in tags):
        raise EngineError(INPUT_INVALID, "topic fact tags must be strings")
    if fact.get("magnitude_bp", 0) not in range(0, 10_001):
        raise EngineError(INPUT_INVALID, "topic fact magnitude_bp is invalid")
    if fact.get("direction", "neutral") not in {"supports", "counters", "neutral"}:
        raise EngineError(INPUT_INVALID, "topic fact direction is invalid")
    consent = fact.get("consent_scope", "self")
    if consent not in {"self", "public_fact", "single_party", "bilateral_analysis"}:
        raise EngineError(INPUT_INVALID, "topic fact consent_scope is invalid")
    normalized = {
        "record_id": record_id,
        "node_type": fact["node_type"],
        "occurred_on": fact.get("occurred_on"),
        "date_precision": fact.get("date_precision", "unknown"),
        "tags": sorted(set(tags)),
        "direction": fact.get("direction", "neutral"),
        "magnitude_bp": int(fact.get("magnitude_bp", 0)),
        "source_reliability_bp": int(fact.get("source_reliability_bp", 6000)),
        "independence_group": str(fact.get("independence_group") or record_id),
        "shared_source_group": str(fact.get("shared_source_group") or record_id),
        "consent_scope": consent,
        "withdrawn": bool(fact.get("withdrawn", False)),
        "deleted": bool(fact.get("deleted", False)),
        "rule_id": str(fact.get("rule_id") or "TOPIC.FACT.NORMALIZE.V1"),
        "rule_version": str(fact.get("rule_version") or "1.0.0"),
        "time_precision": str(fact.get("time_precision") or fact.get("date_precision", "unknown")),
    }
    return {**normalized, "content_hash": content_hash(normalized)}


def _node(node_type: str, payload: dict) -> dict:
    base = {
        "node_type": node_type,
        "source_record_refs": sorted(payload.pop("source_record_refs", [])),
        "time_precision": payload.pop("time_precision", "unknown"),
        "consent_scope": payload.pop("consent_scope", "self"),
        "withdrawn": bool(payload.pop("withdrawn", False)),
        "deleted": bool(payload.pop("deleted", False)),
        "rule_id": payload.pop("rule_id", "TOPIC.GRAPH.V1"),
        "rule_version": payload.pop("rule_version", "1.0.0"),
        **payload,
    }
    node_id = _stable_id("node", base)
    value = {"node_id": node_id, **base}
    return {**value, "content_hash": content_hash(value)}


def _edge(edge_type: str, source: str, target: str, payload: dict) -> dict:
    if edge_type not in EDGE_TYPES:
        raise EngineError(INPUT_INVALID, "topic edge type is not supported")
    base = {
        "edge_type": edge_type,
        "source_node_id": source,
        "target_node_id": target,
        "rule_id": payload.get("rule_id", "TOPIC.GRAPH.V1"),
        "rule_version": payload.get("rule_version", "1.0.0"),
        "source_refs": sorted(payload.get("source_refs", [])),
        "direction": payload.get("direction", edge_type),
        "strength_contribution_bp": int(payload.get("strength_contribution_bp", 0)),
        "confidence_contribution_bp": int(payload.get("confidence_contribution_bp", 0)),
        "trace_ref": payload.get("trace_ref", "trace:graph"),
    }
    edge_id = _stable_id("edge", base)
    value = {"edge_id": edge_id, **base}
    return {**value, "content_hash": content_hash(value)}


def _effective_facts(facts: list[dict]) -> tuple[list[dict], list[dict]]:
    active = [fact for fact in facts if not fact["withdrawn"] and not fact["deleted"]]
    by_source: dict[str, list[dict]] = {}
    for fact in active:
        by_source.setdefault(fact["shared_source_group"], []).append(fact)
    retained, decisions = [], []
    for group in sorted(by_source):
        members = sorted(
            by_source[group],
            key=lambda item: (
                -item["magnitude_bp"] * item["source_reliability_bp"],
                item["record_id"],
                item["content_hash"],
            ),
        )
        retained.append(members[0])
        decisions.append({
            "shared_source_group": group,
            "retained_record_id": members[0]["record_id"],
            "discounted_record_ids": sorted(item["record_id"] for item in members[1:]),
            "policy": "single_strongest_fact_per_shared_source_group",
        })
    return sorted(retained, key=lambda item: item["content_hash"]), decisions


def _score(facts: list[dict], rules: dict) -> dict:
    positive = [item for item in facts if item["direction"] == "supports"]
    negative = [item for item in facts if item["direction"] == "counters"]
    schedule = rules["diminishing_returns_bp"]

    def contribution(items: list[dict]) -> int:
        ordered = sorted(
            items,
            key=lambda item: (-item["magnitude_bp"], item["content_hash"]),
        )
        total = 0
        for index, item in enumerate(ordered):
            factor = schedule[min(index, len(schedule) - 1)]
            total += item["magnitude_bp"] * item["source_reliability_bp"] * factor // 100_000_000
        return min(10_000, total)

    support_bp, counter_bp = contribution(positive), contribution(negative)
    strength_bp = max(0, support_bp - counter_bp)
    groups = sorted({item["independence_group"] for item in positive + negative})
    precision = sum(
        {"exact_date": 1000, "month_only": 700, "year_only": 400}.get(
            item["date_precision"], 200
        )
        for item in positive + negative
    )
    reliability = (
        sum(item["source_reliability_bp"] for item in positive + negative)
        // max(1, len(positive) + len(negative))
    )
    confidence_bp = min(
        10_000,
        len(groups) * 1300 + min(2500, precision) + reliability * 35 // 100,
    )
    conflict_bp = min(support_bp, counter_bp)
    confidence_bp = max(0, confidence_bp - conflict_bp // 2)
    return {
        "support_bp": support_bp,
        "counterevidence_bp": counter_bp,
        "strength_bp": strength_bp,
        "confidence_bp": confidence_bp,
        "independent_evidence_count": len(groups),
        "independence_groups": groups,
        "status": "insufficient",
    }


def _status(score: dict, margin_bp: int, rules: dict) -> str:
    if score["independent_evidence_count"] < rules["thresholds"]["minimum_groups"]:
        return "insufficient"
    if margin_bp < rules["thresholds"]["contested_margin_bp"]:
        return "contested"
    if (
        score["strength_bp"] >= rules["thresholds"]["decisive_strength_bp"]
        and score["confidence_bp"] >= rules["thresholds"]["decisive_confidence_bp"]
    ):
        return "decisive"
    return "provisional"


def _name(seed: dict, names: dict, used: set[str]) -> str:
    profile = names["profiles"].get(seed["culture_profile"], names["profiles"]["generic"])
    for offset in range(64):
        full = (
            str(_pick(profile["surnames"], seed, f"surname:{offset}"))
            + str(_pick(profile["given_names"], seed, f"given:{offset}"))
        )
        if full not in used and full not in names["disabled_combinations"]:
            used.add(full)
            return full
    raise EngineError(INPUT_INVALID, "deterministic naming asset cannot produce a unique name")


def _past_life_candidates(
    seed_hash: str, facts: list[dict], score: dict, rules: dict, names: dict,
    count: int = 3,
) -> list[dict]:
    used: set[str] = set()
    candidates = []
    for index in range(count):
        seed = {
            "canonical_input_hash": seed_hash,
            "topic_ruleset_version": RULESET_VERSION,
            "naming_ruleset_version": NAME_RULESET_VERSION,
            "candidate_index": index + 1,
        }
        era = _pick(rules["past_life"]["eras"], seed, "era")
        region = _pick(rules["past_life"]["regions"], seed, "region")
        gender = _pick(rules["past_life"]["gender_tendencies"], seed, "gender")
        role = _pick(rules["past_life"]["roles"], seed, "role")
        profession = _pick(rules["past_life"]["professions"], seed, "profession")
        culture = region["culture_profile"]
        name_seed = {
            **seed,
            "era": era["id"],
            "region": region["id"],
            "culture_profile": culture,
            "gender_profile": gender,
            "social_role_profile": role,
        }
        inferred_conf = max(800, score["confidence_bp"] - index * 700)
        name_value = _name(name_seed, names, used)
        deaths = []
        for death_rank in range(2):
            cause = _pick(
                rules["past_life"]["death_causes"], seed, f"death:{death_rank}"
            )
            deaths.append({
                "rank": death_rank + 1,
                "cause": _ep(cause, "rule_inferred", max(500, inferred_conf - 1800)),
                "age_range": _ep(
                    [28 + _hash_index(seed, 25, f"age:{death_rank}"),
                     48 + _hash_index(seed, 31, f"age2:{death_rank}")],
                    "rule_inferred",
                    max(500, inferred_conf - 2200),
                ),
                "transition": _ep(
                    "sudden" if cause in {"战乱", "意外", "水灾", "火灾", "暴力冲突"} else "gradual",
                    "rule_inferred",
                    max(500, inferred_conf - 2200),
                ),
            })
        debt_type = _pick(rules["debt_types"], seed, "debt")
        total_lives = 3 + _hash_index(seed_hash, 9, "reincarnation")
        status = "insufficient" if inferred_conf < 3000 else "provisional"
        supporting_ids = [
            fact["record_id"] for fact in facts if fact["direction"] == "supports"
        ]
        counter_ids = [
            fact["record_id"] for fact in facts if fact["direction"] == "counters"
        ]
        candidate = {
            "candidate_id": f"sushe-{index + 1}",
            "rank": index + 1,
            "name": _ep(name_value, "generated_identity", inferred_conf),
            "name_type": "deterministic_generated_identity",
            "gender_tendency": _ep(gender, "rule_inferred", inferred_conf),
            "birth_era": _ep(era["range"], "rule_inferred", inferred_conf),
            "active_era": _ep(era["label"], "rule_inferred", inferred_conf),
            "historical_stage": _ep(era["stage"], "rule_inferred", inferred_conf),
            "culture_region": _ep(region["culture"], "rule_inferred", inferred_conf),
            "region_candidates": _ep(region["candidates"], "rule_inferred", inferred_conf),
            "geography": _ep(region["geography"], "rule_inferred", inferred_conf),
            "settlement_type": _ep(region["settlement"], "rule_inferred", inferred_conf),
            "social_class": _ep(role, "rule_inferred", inferred_conf),
            "identity": _ep(f"{role}中的{profession}", "rule_inferred", inferred_conf),
            "profession": _ep(profession, "rule_inferred", inferred_conf),
            "family_structure": _ep(
                _pick(rules["past_life"]["family_structures"], seed, "family"),
                "rule_inferred", inferred_conf,
            ),
            "important_relationships": _ep(
                _pick(rules["past_life"]["relationships"], seed, "relations"),
                "rule_inferred", inferred_conf,
            ),
            "personality_structure": _ep(
                _pick(rules["past_life"]["personalities"], seed, "personality"),
                "rule_inferred", inferred_conf,
            ),
            "long_term_vow": _ep(
                _pick(rules["past_life"]["vows"], seed, "vow"),
                "rule_inferred", inferred_conf,
            ),
            "key_life_events": _ep(
                _pick(rules["past_life"]["events"], seed, "events"),
                "rule_inferred", inferred_conf,
            ),
            "turning_point": _ep(
                _pick(rules["past_life"]["turning_points"], seed, "turning"),
                "rule_inferred", inferred_conf,
            ),
            "death_candidates": deaths,
            "unfinished_vow": _ep(
                _pick(rules["past_life"]["unfinished"], seed, "unfinished"),
                "rule_inferred", inferred_conf,
            ),
            "causal_debts": [{
                "debt_id": f"debt-{index + 1}-1",
                "type": _ep(debt_type, "rule_inferred", max(500, inferred_conf - 1000)),
                "direction": _ep("owed_by_subject", "rule_inferred", inferred_conf),
                "origin_candidate_id": f"sushe-{index + 1}",
                "formation_reason": _ep("未完成的承诺或责任", "rule_inferred", inferred_conf),
                "present_manifestation": _ep("重复出现的责任主题", "rule_inferred", inferred_conf),
                "current_state": _ep("research_candidate", "rule_inferred", inferred_conf),
                "repayment_state": _ep("unknown", "insufficient", min(2500, inferred_conf)),
                "accumulating": _ep(False, "insufficient", min(2500, inferred_conf)),
                "possible_completion_condition": _ep("完成明确且可撤回的现实承诺", "rule_inferred", inferred_conf),
                "supporting_record_ids": supporting_ids,
                "counterevidence_record_ids": counter_ids,
                "strength_bp": max(300, score["strength_bp"] - index * 600),
                "confidence_bp": max(500, inferred_conf - 1000),
                "status": status,
            }],
            "reincarnation": {
                "main_value": _ep(total_lives, "rule_inferred", inferred_conf),
                "range": _ep([max(1, total_lives - 1), total_lives + 2], "rule_inferred", inferred_conf),
                "focus_position": _ep(index + 1, "rule_inferred", inferred_conf),
                "identifiable_candidates": count,
                "rule_id": "TOPIC.SUSHE.REINCARNATION.V1",
            },
            "present_life_correspondence": _ep(
                _pick(rules["past_life"]["correspondences"], seed, "present"),
                "rule_inferred", inferred_conf,
            ),
            "relationship_continuities": [],
            "historical_person_candidates": [],
            "supporting_record_ids": supporting_ids,
            "counterevidence_record_ids": counter_ids,
            "conflicts": ["support_counterevidence_overlap"] if counter_ids else [],
            "missing_facts": ["independent_historical_source", "traditional_rule_review"],
            "strength_bp": max(0, score["strength_bp"] - index * 700),
            "confidence_bp": inferred_conf,
            "lead_margin_bp": 700 if index < count - 1 else 0,
            "status": status,
            "ruleset_version": RULESET_VERSION,
            "naming_ruleset_version": NAME_RULESET_VERSION,
        }
        candidates.append(candidate)
    return candidates


def _zhongyin_candidate(topic: str, facts: list[dict], score: dict, rules: dict) -> dict:
    if topic == "zhongyin_deceased" and not any(
        "subject_deceased_observed" in fact["tags"] for fact in facts
    ):
        raise EngineError(
            INPUT_INVALID,
            "deceased-transition research requires an observed deceased record",
            {"code": "deceased_subject_required"},
        )
    tags = {tag for fact in facts for tag in fact["tags"]}
    if {"new_vow", "new_role", "new_home"} & tags:
        state = "new_structure_emerging"
    elif {"stalled", "direction_conflict"} & tags:
        state = "transition_stalled"
    elif {"separation", "job_exit", "migration"} & tags:
        state = "old_structure_dissolving"
    else:
        state = "not_enough_to_identify"
    inferred = max(800, score["confidence_bp"])
    return {
        "candidate_id": f"{topic}-1",
        "rank": 1,
        "mode": topic,
        "transition_state": _ep(state, "rule_inferred", inferred),
        "old_structure": _ep(sorted(tags & {"job_exit", "separation", "old_role"}), "rule_inferred", inferred),
        "unfinished_matters": _ep(sorted(tags & {"unfinished_vow", "unfulfilled_commitment"}), "rule_inferred", inferred),
        "new_structure_clues": _ep(sorted(tags & {"new_vow", "new_role", "new_home"}), "rule_inferred", inferred),
        "pull_factors": _ep(sorted(tags & {"relationship_echo", "family_duty", "unfinished_vow"}), "rule_inferred", inferred),
        "blocking_factors": _ep(sorted(tags & {"stalled", "direction_conflict", "repeated_interruption"}), "rule_inferred", inferred),
        "time_range": _ep("由记录日期精度限定的过渡窗口", "rule_inferred", inferred),
        "boundary_sensitivity": _ep(any(f["date_precision"] != "exact_date" for f in facts), "mechanically_derived", inferred),
        "supporting_record_ids": [f["record_id"] for f in facts if f["direction"] == "supports"],
        "counterevidence_record_ids": [f["record_id"] for f in facts if f["direction"] == "counters"],
        "conflicts": ["direction_conflict"] if "direction_conflict" in tags else [],
        "missing_facts": [] if facts else ["transition_records"],
        "strength_bp": score["strength_bp"],
        "confidence_bp": score["confidence_bp"],
        "status": score["status"],
        "no_future_death_prediction": True,
    }


def _yuanqi_candidate(seed_hash: str, facts: list[dict], score: dict, rules: dict, names: dict) -> dict:
    bilateral = any(f["consent_scope"] == "bilateral_analysis" for f in facts)
    tags = {tag for fact in facts for tag in fact["tags"]}
    state = (
        "relationship_ended" if "relationship_ended" in tags
        else "repeated_conflict" if "repeated_conflict" in tags
        else "mutual_response" if bilateral and "mutual_response" in tags
        else "one_way_pull"
    )
    used: set[str] = set()
    identities = []
    for side in ("subject", "related_party"):
        seed = {
            "canonical_input_hash": seed_hash,
            "topic_ruleset_version": RULESET_VERSION,
            "naming_ruleset_version": NAME_RULESET_VERSION,
            "candidate_index": side,
            "era": "generic_historical_range",
            "region": "generic_chinese_region",
            "culture_profile": "zh_historical",
            "gender_profile": "unspecified",
            "social_role_profile": "relationship_counterpart",
        }
        identities.append({
            "side": side,
            "name": _ep(_name(seed, names, used), "generated_identity", max(700, score["confidence_bp"] - 1200)),
        })
    trend = (
        "relationship_continues_to_dissipate" if state == "relationship_ended"
        else "evidence_remains_contested" if score["status"] == "contested"
        else "response_trend_increases" if bilateral else "single_party_observation_only"
    )
    return {
        "candidate_id": "yuanqi-1",
        "rank": 1,
        "observation_scope": "bilateral_structure" if bilateral else "single_party_relationship_observation",
        "relationship_type": _ep(_pick(rules["relationship_types"], seed_hash, "relation"), "rule_inferred", score["confidence_bp"]),
        "relationship_stage": _ep(state, "rule_inferred", score["confidence_bp"]),
        "mutual_response": _ep("confirmed" if bilateral else "not_confirmed", "observed", score["confidence_bp"]),
        "commitments_and_actions": _ep(sorted(tags & {"commitment", "action", "unfulfilled_commitment"}), "rule_inferred", score["confidence_bp"]),
        "conflict_themes": _ep(sorted(tags & {"repeated_conflict", "withdrawal", "avoidance"}), "rule_inferred", score["confidence_bp"]),
        "maintenance_factors": _ep(sorted(tags & {"mutual_response", "sustained_action"}), "rule_inferred", score["confidence_bp"]),
        "dissipation_factors": _ep(sorted(tags & {"withdrawal", "relationship_ended", "unfulfilled_commitment"}), "rule_inferred", score["confidence_bp"]),
        "past_life_identity_candidates": identities,
        "past_life_relationship_type": _ep(_pick(rules["past_relationship_types"], seed_hash, "past_relation"), "rule_inferred", max(700, score["confidence_bp"] - 1500)),
        "causal_debts": [{
            "debt_id": "yuanqi-debt-1",
            "type": _ep(_pick(rules["debt_types"], seed_hash, "relation_debt"), "rule_inferred", max(600, score["confidence_bp"] - 1000)),
            "direction": _ep("between_recorded_parties", "rule_inferred", score["confidence_bp"]),
            "supporting_record_ids": [f["record_id"] for f in facts if f["direction"] == "supports"],
            "strength_bp": score["strength_bp"],
            "confidence_bp": max(600, score["confidence_bp"] - 1000),
        }],
        "unfinished_promise": _ep("unfulfilled_commitment" in tags, "rule_inferred", score["confidence_bp"]),
        "present_correspondence": _ep("现实互动、承诺与撤回记录", "rule_inferred", score["confidence_bp"]),
        "current_state": _ep(state, "rule_inferred", score["confidence_bp"]),
        "future_trend": _ep(trend, "rule_inferred", max(600, score["confidence_bp"] - 1200)),
        "supporting_record_ids": [f["record_id"] for f in facts if f["direction"] == "supports"],
        "counterevidence_record_ids": [f["record_id"] for f in facts if f["direction"] == "counters"],
        "conflicts": ["commitment_action_mismatch"] if {"commitment", "unfulfilled_commitment"} <= tags else [],
        "missing_facts": [] if bilateral else ["bilateral_analysis_consent"],
        "strength_bp": score["strength_bp"],
        "confidence_bp": score["confidence_bp"],
        "status": score["status"],
        "absolute_reunion_claim": False,
        "destined_partner_claim": False,
    }


def _build_graph(
    topic: str, subject_id: str, facts: list[dict], candidates: list[dict],
    score: dict, rules: dict,
) -> dict:
    subject = _node("subject", {
        "source_record_refs": [subject_id],
        "epistemic_status": "observed",
        "topic_type": topic,
    })
    nodes = [subject]
    edges = []
    fact_nodes = {}
    for fact in facts:
        node = _node(fact["node_type"], {
            "source_record_refs": [fact["record_id"]],
            "time_precision": fact["time_precision"],
            "consent_scope": fact["consent_scope"],
            "withdrawn": fact["withdrawn"],
            "deleted": fact["deleted"],
            "rule_id": fact["rule_id"],
            "rule_version": fact["rule_version"],
            "tags": fact["tags"],
            "epistemic_status": (
                "mechanically_derived"
                if fact["node_type"] == "mechanical_chart_reference"
                else "observed"
            ),
        })
        nodes.append(node)
        fact_nodes[fact["record_id"]] = node
        edges.append(_edge("involves", node["node_id"], subject["node_id"], {
            "source_refs": [fact["record_id"]],
            "confidence_contribution_bp": fact["source_reliability_bp"],
        }))
    for candidate in candidates:
        candidate_node = _node("topic_candidate", {
            "source_record_refs": [],
            "rule_id": "TOPIC.CANDIDATE.V1",
            "candidate_id": candidate["candidate_id"],
            "epistemic_status": "rule_inferred",
        })
        nodes.append(candidate_node)
        for fact in facts:
            edge_type = (
                "supports" if fact["direction"] == "supports"
                else "counters" if fact["direction"] == "counters"
                else "corresponds_to"
            )
            edges.append(_edge(
                edge_type, fact_nodes[fact["record_id"]]["node_id"],
                candidate_node["node_id"], {
                    "source_refs": [fact["record_id"]],
                    "strength_contribution_bp": fact["magnitude_bp"],
                    "confidence_contribution_bp": fact["source_reliability_bp"],
                },
            ))
        if topic in {"sushe", "yuanqi"}:
            identity_values = (
                [candidate["name"]]
                if topic == "sushe"
                else [item["name"] for item in candidate["past_life_identity_candidates"]]
            )
            for identity in identity_values:
                identity_node = _node("identity_candidate", {
                    "source_record_refs": [],
                    "rule_id": "TOPIC.NAME.DETERMINISTIC.V1",
                    "epistemic_status": "generated_identity",
                    "generated_name": identity["value"],
                })
                nodes.append(identity_node)
                edges.append(_edge(
                    "derived_from", candidate_node["node_id"], identity_node["node_id"],
                    {"strength_contribution_bp": 0, "confidence_contribution_bp": identity["confidence_bp"]},
                ))
    nodes = sorted(nodes, key=lambda item: item["node_id"])
    edges = sorted(edges, key=lambda item: item["edge_id"])
    base = {
        "schema_version": "topic-evidence-graph/1.0.0",
        "topic_type": topic,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "support_summary": {
            "edges": sum(1 for edge in edges if edge["edge_type"] == "supports"),
            "strength_bp": score["support_bp"],
        },
        "counterevidence_summary": {
            "edges": sum(1 for edge in edges if edge["edge_type"] == "counters"),
            "strength_bp": score["counterevidence_bp"],
        },
        "conflict_summary": {"count": sum(1 for edge in edges if edge["edge_type"] == "conflicts_with")},
        "missing_summary": {"count": sum(1 for node in nodes if node["node_type"] == "missing_fact")},
    }
    return {**base, "graph_hash": content_hash(base)}


def run_topic_research_v1(snapshot: dict) -> tuple[dict, list[dict]]:
    if snapshot.get("operation") != OPERATION:
        raise EngineError(INPUT_INVALID, "topic research operation is not supported")
    topic = snapshot.get("topic_type")
    if topic not in TOPICS:
        raise EngineError(INPUT_INVALID, "topic_type is not supported")
    subject_id = snapshot.get("subject_id")
    if not isinstance(subject_id, str) or not subject_id:
        raise EngineError(INPUT_INVALID, "topic research requires subject_id")
    external_model_fields = ("deep" + "seek", "llm", "oracle", "embedding")
    if any(key in snapshot for key in external_model_fields):
        raise EngineError(INPUT_INVALID, "external model fields are forbidden")
    raw_facts = snapshot.get("facts", [])
    if not isinstance(raw_facts, list):
        raise EngineError(INPUT_INVALID, "topic facts must be an array")
    rules_asset, names_asset = load_topic_assets()
    rules = rules_asset["rules"]
    facts = sorted((_normalize_fact(item) for item in raw_facts), key=lambda item: item["content_hash"])
    retained, deduplication = _effective_facts(facts)
    score = _score(retained, rules)
    input_seed = content_hash({
        "topic_type": topic,
        "subject_id": subject_id,
        "relationship_id": snapshot.get("relationship_id"),
        "profile_id": snapshot.get("profile_id"),
        "facts": facts,
        "topic_ruleset_version": RULESET_VERSION,
        "naming_ruleset_version": NAME_RULESET_VERSION,
    })
    if topic == "sushe":
        candidates = _past_life_candidates(
            input_seed, retained, score, rules, names_asset, 3
        )
    elif topic.startswith("zhongyin"):
        candidates = [_zhongyin_candidate(topic, retained, score, rules)]
    else:
        candidates = [_yuanqi_candidate(input_seed, retained, score, rules, names_asset)]
    margin = (
        max(0, candidates[0]["strength_bp"] - candidates[1]["strength_bp"])
        if len(candidates) > 1 else score["strength_bp"]
    )
    overall_status = _status(score, margin, rules)
    score["status"] = overall_status
    for candidate in candidates:
        candidate["status"] = overall_status
    graph = _build_graph(topic, subject_id, retained, candidates, score, rules)
    trace_base = [
        {
            "step_id": "topic:100:normalize",
            "module_id": "signals",
            "operation": "normalize_authorized_topic_facts",
            "input_refs": [f"record:{fact['record_id']}" for fact in facts],
            "output_refs": [f"fact:{fact['content_hash']}" for fact in retained],
            "rule_refs": ["TOPIC.FACT.NORMALIZE.V1"],
            "calculation": {"input_count": len(facts), "retained_count": len(retained)},
        },
        {
            "step_id": "topic:200:graph",
            "module_id": "signals",
            "operation": "build_canonical_topic_evidence_graph",
            "input_refs": [f"fact:{fact['content_hash']}" for fact in retained],
            "output_refs": [f"graph:{graph['graph_hash']}"],
            "rule_refs": ["TOPIC.GRAPH.V1"],
            "calculation": {"node_count": graph["node_count"], "edge_count": graph["edge_count"]},
        },
        {
            "step_id": "topic:300:infer",
            "module_id": "inference",
            "operation": "generate_rank_and_label_topic_candidates",
            "input_refs": [f"graph:{graph['graph_hash']}"],
            "output_refs": [f"candidate:{item['candidate_id']}" for item in candidates],
            "rule_refs": [RULESET_VERSION, NAME_RULESET_VERSION],
            "calculation": deepcopy(score),
        },
    ]
    trace = [{**step, "content_hash": content_hash(step)} for step in trace_base]
    topic_trace_hash = content_hash(trace)
    for candidate in candidates:
        candidate["candidate_output_hash"] = content_hash(candidate)
        candidate["trace_hash"] = topic_trace_hash
    result_base = {
        "schema_version": "topic-result/1.0.0",
        "tradition_scope": "sanji_original",
        "activation": "research_active",
        "review_status": "UNCONFIRMED",
        "production_activatable": False,
        "engine_version": __version__,
        "topic_type": topic,
        "epistemic_model_version": "topic-epistemic-status/1.0.0",
        "topic_ruleset_version": RULESET_VERSION,
        "topic_ruleset_hash": rules_asset["content_hash"],
        "naming_ruleset_version": NAME_RULESET_VERSION,
        "naming_ruleset_hash": names_asset["content_hash"],
        "evidence_policy_version": "liuxiang-user-evidence-policy/1.0.0",
        "canonical_input_hash": input_seed,
        "graph": graph,
        "candidates": candidates,
        "deduplication": deduplication,
        "supporting_record_ids": [f["record_id"] for f in retained if f["direction"] == "supports"],
        "counterevidence_record_ids": [f["record_id"] for f in retained if f["direction"] == "counters"],
        "conflicts": ["support_counterevidence_overlap"] if score["counterevidence_bp"] else [],
        "missing_facts": ["minimum_independent_records"] if score["independent_evidence_count"] < rules["thresholds"]["minimum_groups"] else [],
        "strength_bp": score["strength_bp"],
        "confidence_bp": score["confidence_bp"],
        "status": overall_status,
        "trace_ref": "trace:topic",
        "no_llm_or_oracle_input": True,
        "historical_claim": False,
    }
    return {**result_base, "result_hash": content_hash(result_base)}, trace
