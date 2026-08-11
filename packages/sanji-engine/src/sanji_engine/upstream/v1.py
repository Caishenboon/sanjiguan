"""Deterministic composition of already-computed pinned upstream results.

This module never imports an upstream package. Adapters are an outer boundary;
the engine validates their provenance and forms a canonical evidence graph.
"""
from __future__ import annotations

from copy import deepcopy

from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID

OPERATION = "compose_upstream_traditional_v1"
METHOD_ID = "SANJI.UPSTREAM.COMPOSITE.RESEARCH.V1"
ALLOWED = {
    "6tail/lunar-python": ("1.4.8", "000c8a3d74eed098d6256a28fdd51b869324c559", "MIT"),
    "SylarLong/iztro": ("2.5.8", "9d39f1743bf31c2b3c635c9b9556215d9c90ee2c", "MIT"),
    "yaomancy/liuyao-engine": ("0.1.0", "562b902eb3ec47d4dadb326b6dc98e8ee09b4295", "Apache-2.0"),
}


def _validate_adapter(item: dict) -> dict:
    required = {"schema_version", "upstream_name", "upstream_version", "upstream_commit",
                "license", "adapter_version", "method_profile", "canonical_input", "output",
                "warnings", "disputes", "trace", "raw_hash", "canonical_hash"}
    if not isinstance(item, dict) or required - item.keys():
        raise EngineError(INPUT_INVALID, "upstream adapter result is incomplete")
    expected = ALLOWED.get(item["upstream_name"])
    if expected != (item["upstream_version"], item["upstream_commit"], item["license"]):
        raise EngineError(INPUT_INVALID, "upstream identity does not match the admitted lock")
    projection = {key: deepcopy(value) for key, value in item.items() if key != "canonical_hash"}
    if content_hash(projection) != item["canonical_hash"]:
        raise EngineError(INPUT_INVALID, "upstream adapter canonical hash mismatch")
    return deepcopy(item)


def compose_upstream_traditional_v1(snapshot: dict) -> tuple[dict, list[dict]]:
    if snapshot.get("operation") != OPERATION:
        raise EngineError(INPUT_INVALID, "unsupported upstream composition operation")
    values = snapshot.get("adapter_results")
    if not isinstance(values, list) or not values:
        raise EngineError(INPUT_INVALID, "adapter_results must be a non-empty list")
    admitted = [_validate_adapter(item) for item in values]
    admitted.sort(key=lambda item: (item["upstream_name"], item["canonical_hash"]))
    unique=[]; seen=set()
    for item in admitted:
        if item["canonical_hash"] not in seen:
            unique.append(item); seen.add(item["canonical_hash"])
    admitted=unique

    nodes, edges, disputes = [], [], []
    source_counts={name:sum(item["upstream_name"]==name for item in admitted)
                   for name in {item["upstream_name"] for item in admitted}}
    for index, item in enumerate(admitted, 1):
        source_id = f"source:{index:02d}:{item['upstream_name']}"
        fact_id = f"fact:{index:02d}:{item['raw_hash']}"
        nodes.extend([
            {"node_id": source_id, "node_type": "upstream_source", "content_hash": content_hash({
                "name": item["upstream_name"], "version": item["upstream_version"], "commit": item["upstream_commit"]})},
            {"node_id": fact_id, "node_type": "mechanical_fact_set", "content_hash": item["raw_hash"],
             "upstream": item["upstream_name"], "independence_group": item["upstream_name"]},
        ])
        edges.append({"edge_id": f"edge:{index:02d}", "edge_type": "derived_from",
                      "from": fact_id, "to": source_id, "mapping": item["adapter_version"]})
        disputes.extend({"upstream": item["upstream_name"], **entry} for entry in item["disputes"])
    disputes.extend({"upstream":name,"field":"same_source_multiple_results","status":"conflict",
                     "result_count":count} for name,count in source_counts.items() if count>1)
    graph = {"schema_version": "canonical-evidence-graph/1.0.0",
             "nodes": sorted(nodes, key=lambda x: x["node_id"]),
             "edges": sorted(edges, key=lambda x: x["edge_id"])}
    result = {
        "tradition_scope": "pinned_upstream_research",
        "activation": "research_active", "review_status": "UNCONFIRMED",
        "production_activatable": False,
        "ruleset_version": "sanji-upstream-composite-1.0.0",
        "adapter_results": admitted,
        "evidence_graph": {**graph, "graph_hash": content_hash(graph)},
        "deduplication": {"policy": "same_upstream_and_raw_hash_is_one_independence_group",
                          "independent_source_count": len(source_counts),
                          "exact_duplicate_count": len(values)-len(admitted)},
        "disputes": sorted(disputes, key=lambda x: (x["upstream"], x.get("field", ""))),
        "strength_bp": 0, "confidence_bp": 0, "status": "insufficient",
        "status_reason": "No reviewed interpretive mapping or scoring rule is admitted; mechanical facts do not imply a verdict.",
    }
    trace = [
        {"step_id": "upstream:01:validate-lock", "module_id": "upstream", "rule_id": METHOD_ID,
         "input_hashes": [item["canonical_hash"] for item in admitted]},
        {"step_id": "upstream:02:canonical-graph", "module_id": "upstream", "rule_id": METHOD_ID,
         "graph_hash": result["evidence_graph"]["graph_hash"]},
        {"step_id": "upstream:03:no-interpretive-score", "module_id": "upstream", "rule_id": METHOD_ID,
         "strength_bp": 0, "confidence_bp": 0, "status": "insufficient"},
    ]
    return {**result, "result_hash": content_hash(result)}, trace
