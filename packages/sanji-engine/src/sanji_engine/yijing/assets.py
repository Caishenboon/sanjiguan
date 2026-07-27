from __future__ import annotations

import json
from importlib.resources import files

from ..canonical import content_hash
from ..errors import EngineError, REPLAY_ASSET_MISSING

ASSET_VERSION = "king-wen-hexagrams/1.0.0"
ASSET_FILE = "king-wen-hexagrams-1.0.0.json"


def load_hexagrams() -> tuple[dict[str, dict], dict]:
    try:
        asset = json.loads(
            files("sanji_engine").joinpath(f"yijing/assets/{ASSET_FILE}").read_text("utf-8")
        )
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise EngineError(REPLAY_ASSET_MISSING, "hexagram mapping asset unavailable") from exc
    items = asset.get("hexagrams", [])
    keys = [item["key"] for item in items]
    sequences = [item["sequence"] for item in items]
    names = [item["name"] for item in items]
    if (
        asset.get("asset_version") != ASSET_VERSION
        or len(items) != 64
        or len(set(keys)) != 64
        or sorted(sequences) != list(range(1, 65))
        or len(set(names)) != 64
    ):
        raise EngineError(REPLAY_ASSET_MISSING, "hexagram mapping asset failed integrity checks")
    for item in items:
        if item["key"] != item["lower_trigram"]["key"] + item["upper_trigram"]["key"]:
            raise EngineError(REPLAY_ASSET_MISSING, "hexagram trigram structure mismatch")
    projection = {key: value for key, value in asset.items() if key != "content_hash"}
    actual_hash = content_hash(projection)
    if asset.get("content_hash") != actual_hash:
        raise EngineError(REPLAY_ASSET_MISSING, "hexagram mapping asset hash mismatch")
    return {item["key"]: item for item in items}, {
        "asset_version": ASSET_VERSION,
        "content_hash": actual_hash,
        "source_ids": asset["source_ids"],
        "review_status": asset["review_status"],
    }
