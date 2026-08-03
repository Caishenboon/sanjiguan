"""Canonical composition for the three pinned traditional research profiles."""
from __future__ import annotations

from copy import deepcopy

from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID
from ..upstream.v1 import ALLOWED

OPERATION = "compose_traditional_algorithms_complete_v1"
METHOD_ID = "SANJI.TRADITIONAL.COMPOSITE.V1"
RULESET_ID = "sanji-traditional-composite-1.0.0"
PROFILE_BY_SOURCE = {
    "6tail/lunar-python": ("bazi-ziping-complete-v1", "bazi-ziping-complete-1.0.0"),
    "SylarLong/iztro": ("ziwei-sanhe-complete-v1", "ziwei-sanhe-complete-1.0.0"),
    "yaomancy/liuyao-engine": ("liuyao-jingfang-najia-v1", "liuyao-jingfang-najia-1.0.0"),
}


def _validate(item: dict) -> dict:
    required = {"upstream_name", "upstream_version", "upstream_commit", "license",
                "method_profile", "output", "canonical_hash"}
    if not isinstance(item, dict) or required - item.keys():
        raise EngineError(INPUT_INVALID, "complete traditional adapter result is incomplete")
    expected = ALLOWED.get(item["upstream_name"])
    if expected != (item["upstream_version"], item["upstream_commit"], item["license"]):
        raise EngineError(INPUT_INVALID, "complete traditional upstream identity is not admitted")
    projection = {key: deepcopy(value) for key, value in item.items() if key != "canonical_hash"}
    if content_hash(projection) != item["canonical_hash"]:
        raise EngineError(INPUT_INVALID, "complete traditional adapter hash mismatch")
    profile_id, ruleset_id = PROFILE_BY_SOURCE[item["upstream_name"]]
    if item["method_profile"].get("profile_id") != profile_id:
        raise EngineError(INPUT_INVALID, f"explicit complete profile required: {profile_id}")
    complete = item["output"].get("complete_v1")
    if not isinstance(complete, dict) or complete.get("ruleset_version") != ruleset_id:
        raise EngineError(INPUT_INVALID, "adapter did not provide its complete V1 canonical result")
    return deepcopy(item)


def _system_metrics(item: dict) -> tuple[int, int, str]:
    result = item["output"]["complete_v1"]
    if item["upstream_name"] == "6tail/lunar-python":
        return result["strength"]["balance_bp"], result["strength"]["confidence_bp"], result["strength"]["status"]
    if item["upstream_name"] == "SylarLong/iztro":
        palaces = result["palaces"]
        strength = sum(p["strength_bp"] for p in palaces) // max(1, len(palaces))
        confidence = sum(p["confidence_bp"] for p in palaces) // max(1, len(palaces))
        return strength, confidence, "contested" if any(p["status"] == "contested" for p in palaces) else "provisional"
    return result["strength_bp"], result["confidence_bp"], result["verdict"]


def compose_traditional_complete_v1(snapshot: dict) -> tuple[dict, list[dict]]:
    if snapshot.get("operation") != OPERATION:
        raise EngineError(INPUT_INVALID, "unsupported complete traditional operation")
    values = snapshot.get("adapter_results")
    if not isinstance(values, list) or not values:
        raise EngineError(INPUT_INVALID, "adapter_results must be non-empty")
    admitted = sorted((_validate(value) for value in values), key=lambda x: x["upstream_name"])
    if len({x["upstream_name"] for x in admitted}) != len(admitted):
        raise EngineError(INPUT_INVALID, "only one result per pinned upstream is allowed")

    nodes, edges, systems = [], [], []
    for index, item in enumerate(admitted, 1):
        complete = item["output"]["complete_v1"]
        strength, confidence, status = _system_metrics(item)
        system_id = {"6tail/lunar-python": "bazi", "SylarLong/iztro": "ziwei",
                     "yaomancy/liuyao-engine": "liuyao"}[item["upstream_name"]]
        source_id, fact_id, result_id = f"source:{system_id}", f"facts:{system_id}", f"result:{system_id}"
        nodes += [
            {"node_id": source_id, "node_type": "upstream_source", "content_hash": content_hash({"name": item["upstream_name"], "commit": item["upstream_commit"]})},
            {"node_id": fact_id, "node_type": "mechanical_fact_set", "content_hash": item["raw_hash"], "independence_group": item["upstream_name"]},
            {"node_id": result_id, "node_type": "traditional_profile_result", "content_hash": content_hash(complete), "ruleset": complete["ruleset_version"]},
        ]
        edges += [
            {"edge_id": f"edge:{index}:source", "edge_type": "derived_from", "from": fact_id, "to": source_id},
            {"edge_id": f"edge:{index}:profile", "edge_type": "derived_from", "from": result_id, "to": fact_id},
        ]
        systems.append({"system": system_id, "upstream": item["upstream_name"],
                        "profile_id": complete["profile_id"], "ruleset_version": complete["ruleset_version"],
                        "strength_bp": strength, "confidence_bp": confidence, "status": status,
                        "result": complete, "canonical_hash": item["canonical_hash"]})
    graph = {"schema_version": "canonical-evidence-graph/1.0.0",
             "nodes": sorted(nodes, key=lambda x: x["node_id"]),
             "edges": sorted(edges, key=lambda x: x["edge_id"])}
    signs = {0 if s["strength_bp"] == 0 else 1 if s["strength_bp"] > 0 else -1 for s in systems}
    strength = sum(s["strength_bp"] for s in systems) // len(systems)
    confidence = sum(s["confidence_bp"] for s in systems) // len(systems)
    if len(systems) < 2:
        state = "insufficient"
    elif len(signs - {0}) > 1:
        state = "contested"
    elif confidence < 6000:
        state = "provisional"
    else:
        state = "decisive"
    result_base = {
        "schema_version": "sanji-traditional-composite-result/1.0.0",
        "ruleset_version": RULESET_ID, "tradition_scope": "traditional_profiles_plus_sanji_composite",
        "activation": "research_active", "review_status": "UNCONFIRMED", "production_activatable": False,
        "systems": systems, "evidence_graph": {**graph, "graph_hash": content_hash(graph)},
        "deduplication": {"policy": "one_independence_group_per_pinned_upstream_and_mechanical_fact_hash",
                          "independent_source_count": len(systems), "duplicate_contribution_count": 0},
        "strength_bp": strength, "confidence_bp": confidence, "status": state,
        "conflicts": [s["system"] for s in systems if (s["strength_bp"] > 0) != (strength > 0)] if strength else [],
        "missing_systems": sorted({"bazi", "ziwei", "liuyao"} - {s["system"] for s in systems}),
        "warnings": ["Research-only composite; agreement is not proof and disagreement is retained.",
                     "Liuyao participates only when an explicit user divination result is supplied."],
    }
    result = {**result_base, "result_hash": content_hash(result_base)}
    trace = [
        {"step_id": "traditional-v1:01:validate", "module_id": "traditional-complete", "rule_id": METHOD_ID,
         "adapter_hashes": [s["canonical_hash"] for s in systems]},
        {"step_id": "traditional-v1:02:graph", "module_id": "traditional-complete", "rule_id": RULESET_ID,
         "graph_hash": result["evidence_graph"]["graph_hash"]},
        {"step_id": "traditional-v1:03:aggregate", "module_id": "traditional-complete", "rule_id": RULESET_ID,
         "strength_bp": strength, "confidence_bp": confidence, "status": state,
         "tie_breaker": "system_id_ascending"},
    ]
    return result, trace
