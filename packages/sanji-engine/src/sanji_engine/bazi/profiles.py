"""Versioned research-executable BaZi profiles. No hidden default exists."""
from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files

from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID, REPLAY_ASSET_MISSING

REGISTRY_VERSION = "bazi-execution-profiles/1.0.0"
PROFILE_VERSION = "1.0.0"


def _load_asset(name: str) -> dict:
    try:
        return json.loads(
            files("sanji_engine").joinpath(f"bazi/assets/{name}").read_text("utf-8")
        )
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise EngineError(REPLAY_ASSET_MISSING, f"BaZi asset unavailable: {name}") from exc


def execution_profile_registry() -> dict:
    value = _load_asset("execution-profiles-1.0.0.json")
    if value.get("registry_version") != REGISTRY_VERSION:
        raise EngineError(REPLAY_ASSET_MISSING, "BaZi execution profile registry mismatch")
    if value.get("production_activatable") is not False:
        raise EngineError(INPUT_INVALID, "BaZi research profile registry crossed production gate")
    return {**deepcopy(value), "content_hash": content_hash(value)}


def load_execution_profile(profile_id: str, profile_version: str) -> dict:
    registry = execution_profile_registry()
    matches = [
        profile for profile in registry["profiles"]
        if profile["profile_id"] == profile_id and profile["profile_version"] == profile_version
    ]
    if not matches:
        raise EngineError(
            INPUT_INVALID,
            "unknown BaZi method profile ID/version",
            {"profile_id": profile_id, "profile_version": profile_version},
        )
    profile = deepcopy(matches[0])
    allowed_bases = {"civil", "local_mean_solar", "local_apparent_solar"}
    for track in profile.get("time_tracks", []):
        mapping = track.get("pillar_time_basis")
        if (
            not isinstance(mapping, dict)
            or set(mapping) != {"year", "month", "day", "hour"}
            or not set(mapping.values()) <= allowed_bases
        ):
            raise EngineError(INPUT_INVALID, "BaZi profile pillar time bases are incomplete")
    return {**profile, "content_hash": content_hash(profile)}


def day_epoch_asset() -> dict:
    value = _load_asset("day-epoch-1.0.0.json")
    if value.get("asset_version") != "bazi-day-epoch/1.0.0":
        raise EngineError(REPLAY_ASSET_MISSING, "BaZi day epoch asset mismatch")
    return {**deepcopy(value), "content_hash": content_hash(value)}
