"""Signal v2 validation, canonical hashing and source-aware deduplication.

This module is integer-only.  It coexists with ``signals.model`` so frozen
Signal v1 replay remains byte-for-byte compatible.
"""
from __future__ import annotations

from copy import deepcopy

from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID

SCHEMA_VERSION = "signal-v2/1.0.0"
ALLOWED_DIRECTIONS = {"positive", "negative", "neutral"}
ALLOWED_SOURCE_SYSTEMS = {
    "synthetic_conformance", "yijing", "bazi", "ziwei",
    "user_evidence", "external_research",
}
REQUIRED_FIELDS = {
    "signal_id", "subject_id", "dimension_id", "direction", "magnitude_bp",
    "source_system", "source_record_id", "source_fact_path", "source_claim_ids",
    "source_dataset_id", "source_dataset_revision", "mapping_rule_id",
    "mapping_ruleset_version", "profile_id", "source_reliability_bp",
    "mapping_reliability_bp", "independence_group", "shared_source_group",
    "temporal_scope", "supports", "counterevidence", "missingness", "disputes",
    "boundary_sensitivity", "trace_ref", "engine_version",
}


def _bp(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10_000:
        raise EngineError(INPUT_INVALID, f"{path} must be an integer basis-point value")
    return value


def _string(value: object, path: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise EngineError(INPUT_INVALID, f"{path} must be a non-empty string")
    return value


def validate_signal_v2(source: dict, dimensions: set[str]) -> dict:
    if not isinstance(source, dict):
        raise EngineError(INPUT_INVALID, "Signal v2 must be an object")
    missing = sorted(REQUIRED_FIELDS - source.keys())
    unexpected = sorted(source.keys() - REQUIRED_FIELDS - {"schema_version", "content_hash"})
    if missing or unexpected:
        raise EngineError(
            INPUT_INVALID,
            "Signal v2 fields are invalid",
            {"missing": missing, "unexpected": unexpected},
        )
    item = deepcopy(source)
    if item.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
        raise EngineError(INPUT_INVALID, "Signal v2 schema version is unsupported")
    item["schema_version"] = SCHEMA_VERSION
    for field in (
        "signal_id", "subject_id", "dimension_id", "source_record_id",
        "source_fact_path", "mapping_rule_id", "mapping_ruleset_version",
        "independence_group", "shared_source_group", "trace_ref", "engine_version",
    ):
        _string(item[field], field)
    for field in ("source_dataset_id", "source_dataset_revision", "profile_id"):
        _string(item[field], field, nullable=True)
    if item["dimension_id"] not in dimensions:
        raise EngineError(INPUT_INVALID, "Signal v2 dimension is unknown")
    if item["direction"] not in ALLOWED_DIRECTIONS:
        raise EngineError(INPUT_INVALID, "Signal v2 direction is invalid")
    if item["source_system"] not in ALLOWED_SOURCE_SYSTEMS:
        raise EngineError(INPUT_INVALID, "Signal v2 source system is invalid")
    for field in ("magnitude_bp", "source_reliability_bp", "mapping_reliability_bp"):
        item[field] = _bp(item[field], field)
    if not isinstance(item["source_claim_ids"], list) or any(
        not isinstance(value, str) for value in item["source_claim_ids"]
    ):
        raise EngineError(INPUT_INVALID, "source_claim_ids must be a string array")
    item["source_claim_ids"] = sorted(set(item["source_claim_ids"]))
    for field in ("supports", "counterevidence"):
        if not isinstance(item[field], list) or any(not isinstance(v, str) for v in item[field]):
            raise EngineError(INPUT_INVALID, f"{field} must be a string array")
        item[field] = sorted(set(item[field]))
    for field in ("temporal_scope", "missingness", "disputes", "boundary_sensitivity"):
        if not isinstance(item[field], dict):
            raise EngineError(INPUT_INVALID, f"{field} must be an object")
    item.pop("content_hash", None)
    item["content_hash"] = content_hash(item)
    return item


def validate_signals_v2(signals: object, dimensions: set[str]) -> list[dict]:
    if not isinstance(signals, list):
        raise EngineError(INPUT_INVALID, "Signal v2 collection must be an array")
    values = [validate_signal_v2(value, dimensions) for value in signals]
    ids = [value["signal_id"] for value in values]
    if len(ids) != len(set(ids)):
        raise EngineError(INPUT_INVALID, "Signal v2 signal_id values must be unique")
    return sorted(values, key=lambda value: (value["dimension_id"], value["signal_id"]))


def fact_fingerprint(signal: dict) -> str:
    return content_hash({
        "source_system": signal["source_system"],
        "source_record_id": signal["source_record_id"],
        "source_fact_path": signal["source_fact_path"],
        "source_dataset_id": signal["source_dataset_id"],
        "source_dataset_revision": signal["source_dataset_revision"],
        "profile_id": signal["profile_id"],
    })


def mapping_fingerprint(signal: dict) -> str:
    return content_hash({
        "fact_fingerprint": fact_fingerprint(signal),
        "dimension_id": signal["dimension_id"],
        "direction": signal["direction"],
        "mapping_rule_id": signal["mapping_rule_id"],
        "mapping_ruleset_version": signal["mapping_ruleset_version"],
    })


def deduplicate_signals_v2(signals: list[dict]) -> tuple[list[dict], list[dict]]:
    """Retain one deterministic representative per fact+mapping path.

    Independence and shared-source caps are applied by inference.  Keeping that
    separate makes every discarded duplicate and every later discount visible.
    """
    selected: dict[str, dict] = {}
    decisions: list[dict] = []
    for signal in sorted(signals, key=lambda value: value["signal_id"]):
        fingerprint = mapping_fingerprint(signal)
        previous = selected.get(fingerprint)
        retained = previous is None
        if previous is not None:
            current_key = (
                signal["magnitude_bp"],
                signal["source_reliability_bp"],
                signal["mapping_reliability_bp"],
                signal["signal_id"],
            )
            previous_key = (
                previous["magnitude_bp"],
                previous["source_reliability_bp"],
                previous["mapping_reliability_bp"],
                previous["signal_id"],
            )
            if current_key > previous_key:
                selected[fingerprint] = signal
                retained = True
        else:
            selected[fingerprint] = signal
        decisions.append({
            "signal_id": signal["signal_id"],
            "fact_fingerprint": fact_fingerprint(signal),
            "mapping_fingerprint": fingerprint,
            "retained_at_step": retained,
        })
    retained_ids = {value["signal_id"] for value in selected.values()}
    for decision in decisions:
        decision["retained_final"] = decision["signal_id"] in retained_ids
        decision["reason"] = (
            "unique_fact_mapping_path"
            if decision["retained_final"] else "duplicate_fact_mapping_path"
        )
    return (
        sorted(selected.values(), key=lambda value: (value["dimension_id"], value["signal_id"])),
        decisions,
    )
