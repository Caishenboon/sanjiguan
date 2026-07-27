from __future__ import annotations

import json
from importlib.resources import files

from ..canonical import content_hash


def _hash_safe(value):
    if isinstance(value, float):
        return str(value)
    if isinstance(value, dict):
        return {key: _hash_safe(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_hash_safe(child) for child in value]
    return value


def _asset(name: str) -> tuple[object, str]:
    value = json.loads(
        files("sanji_engine")
        .joinpath(f"research_baselines/{name}")
        .read_text(encoding="utf-8")
    )
    # Hash parsed canonical content, not checkout bytes. Git may materialize
    # JSON as LF or CRLF, but those transport line endings are not domain data.
    return value, content_hash(_hash_safe(value))


def load_research_assets() -> tuple[list[dict], dict, dict[str, str]]:
    archetypes, archetypes_hash = _asset("archetypes-0.1.0.json")
    config, config_hash = _asset("scoring-config-0.1.0.json")
    return archetypes, config, {
        "archetypes": archetypes_hash,
        "scoring_config": config_hash,
    }
