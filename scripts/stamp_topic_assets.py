"""Stamp deterministic content hashes for Sprint 17 rule assets."""
from __future__ import annotations

import json
from pathlib import Path

from sanji_engine.canonical import content_hash

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "packages/sanji-engine/src/sanji_engine/rulesets/assets"
ASSETS = (
    "topic-research-rules-1.0.0.json",
    "past-life-name-rules-1.0.0.json",
)


def main() -> None:
    for filename in ASSETS:
        path = ASSET_DIR / filename
        value = json.loads(path.read_text(encoding="utf-8"))
        value["content_hash"] = content_hash(
            {key: item for key, item in value.items() if key != "content_hash"}
        )
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{filename}: {value['content_hash']}")


if __name__ == "__main__":
    main()
