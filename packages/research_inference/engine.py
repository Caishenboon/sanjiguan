"""Legacy presentation adapter for sanji-engine research baseline.

This module intentionally contains no scoring, weighting, candidate, ranking,
conflict, or verdict logic. New application code should use sanji_engine.execute.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from sanji_engine import execute


def stable_hash(value) -> str:
    """Legacy persistence hash retained for non-domain application records."""
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def _encode_binary_floats(value):
    if isinstance(value, float):
        return str(value)
    if isinstance(value, dict):
        return {key: _encode_binary_floats(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_encode_binary_floats(child) for child in value]
    return value


_FLOAT_FIELDS = {
    "strength",
    "source_reliability",
    "relevance",
    "raw_score",
    "net_effect",
    "value",
}


def _decode_legacy_numerics(value, parent_key: str | None = None):
    if isinstance(value, dict):
        decoded = {}
        for key, child in value.items():
            if parent_key == "weights" and isinstance(child, str):
                decoded[key] = float(child)
            elif key in _FLOAT_FIELDS and isinstance(child, str):
                decoded[key] = float(child)
            else:
                decoded[key] = _decode_legacy_numerics(child, key)
        return decoded
    if isinstance(value, list):
        return [_decode_legacy_numerics(child, parent_key) for child in value]
    return value


def run_inference(case: dict, archetypes: list[dict], config: dict) -> dict:
    """Return the exact legacy application shape through Engine API 1.0.

    The archetypes/config arguments remain for source compatibility. Their
    versions are verified against the frozen Engine bundle; they are not used
    to perform an application-side calculation.
    """
    if config.get("version") != "0.1.0-research":
        raise ValueError("research_ruleset_version_mismatch")
    if not isinstance(archetypes, list) or not archetypes:
        raise ValueError("research_archetype_asset_missing")
    request = {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": "legacy-research-adapter",
        "run_mode": "research_preview",
        "requested_modules": ["signals", "inference"],
        "input_snapshot": {
            "operation": "run_research_inference",
            "case": _encode_binary_floats(deepcopy(case)),
        },
        "ruleset_bundle_id": "research-baseline-0.2.0",
        "data_versions": {
            "tzdb": "not_used",
            "ephemeris": "not_used",
            "calendar_dataset": "not_used",
            "research_archetypes": "0.1.0-research",
            "research_scoring": "0.1.0-research",
        },
        "deterministic_context": {
            "as_of": "2000-01-01T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
    }
    envelope = execute(request)
    signals = envelope["module_results"]["signals"]["result"]
    inference = envelope["module_results"]["inference"]["result"]
    return {
        "input_hash": signals["legacy_input_hash"],
        "signals": _decode_legacy_numerics(signals["signals"]),
        "weights": _decode_legacy_numerics(signals["weights"], "weights"),
        "locked_verdict": _decode_legacy_numerics(inference["locked_verdict"]),
        "locked_hash": inference["legacy_locked_hash"],
        "stages": inference["legacy_stages"],
        "notice": "研究成断，尚未进入生产规则。",
    }
