"""Stamp deterministic hashes on the Sprint 16 Liuxiang evidence assets."""
from __future__ import annotations

import json
from pathlib import Path

from sanji_engine.canonical import content_hash


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "packages" / "sanji-engine" / "src" / "sanji_engine" / "rulesets" / "assets"
FILES = (
    "liuxiang-evidence-policies-1.0.0.json",
    "liuxiang-evidence-mappings-1.0.0.json",
    "liuxiang-evidence-inference-policy-1.0.0.json",
)


def main() -> None:
    for name in FILES:
        path = ASSETS / name
        value = json.loads(path.read_text(encoding="utf-8"))
        for collection in ("policies", "rules"):
            for item in value.get(collection, []):
                item["content_hash"] = content_hash({
                    key: child for key, child in item.items() if key != "content_hash"
                })
        value["content_hash"] = content_hash({
            key: child for key, child in value.items() if key != "content_hash"
        })
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
