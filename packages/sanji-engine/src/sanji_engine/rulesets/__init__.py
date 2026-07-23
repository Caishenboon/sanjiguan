from __future__ import annotations

import json
from importlib.resources import files

from ..canonical import content_hash
from ..errors import EngineError, RULESET_NOT_FOUND


def load_bundle(bundle_id: str) -> dict:
    registry = json.loads(
        files("sanji_engine").joinpath("rulesets/registry.json").read_text(encoding="utf-8")
    )
    filename = registry.get("bundles", {}).get(bundle_id)
    if not filename:
        raise EngineError(RULESET_NOT_FOUND, f"unknown ruleset bundle: {bundle_id}")
    bundle = json.loads(
        files("sanji_engine").joinpath(f"rulesets/{filename}").read_text(encoding="utf-8")
    )
    return {**bundle, "bundle_hash": content_hash(bundle)}
