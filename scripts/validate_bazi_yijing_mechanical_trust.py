from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "packages/sanji-engine/src/sanji_engine/bazi/assets/mechanical-trust-profiles-1.0.0.json",
    "packages/sanji-engine/src/sanji_engine/bazi/assets/day-epoch-evidence-1.0.0.json",
    "packages/sanji-engine/src/sanji_engine/golden_cases/bazi/mechanical-trust-goldens-1.0.0.json",
    "packages/sanji-engine/src/sanji_engine/yijing/assets/coin-value-profile-1.0.0.json",
    "docs/methods/bazi-yijing-mechanical-trust-v1.md",
]


def main() -> int:
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            raise SystemExit(f"missing trust asset: {relative}")
    profiles = json.loads((ROOT / REQUIRED[0]).read_text("utf-8"))
    if profiles["production_activatable"] or profiles["review_status"] != "UNCONFIRMED":
        raise SystemExit("research profile crossed activation gate")
    evidence = json.loads((ROOT / REQUIRED[1]).read_text("utf-8"))
    if evidence["source_assessment"]["sexagenary_anchor_source_status"] != "UNCONFIRMED":
        raise SystemExit("unconfirmed day epoch was promoted")
    coin = json.loads((ROOT / REQUIRED[3]).read_text("utf-8"))
    if coin["canonical_contract"]["allowed_single_coin_values"] != [2, 3]:
        raise SystemExit("coin numeric contract drifted")
    print("bazi/yijing mechanical trust validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
