from __future__ import annotations

import hashlib
import json
from importlib.resources import files


def _asset(name: str) -> tuple[object, str]:
    raw = (
        files("sanji_engine")
        .joinpath(f"research_baselines/{name}")
        .read_bytes()
    )
    return json.loads(raw), f"sha256:{hashlib.sha256(raw).hexdigest()}"


def load_research_assets() -> tuple[list[dict], dict, dict[str, str]]:
    archetypes, archetypes_hash = _asset("archetypes-0.1.0.json")
    config, config_hash = _asset("scoring-config-0.1.0.json")
    return archetypes, config, {
        "archetypes": archetypes_hash,
        "scoring_config": config_hash,
    }
