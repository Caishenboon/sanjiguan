from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "packages/sanji-engine/src/sanji_engine/ziwei/assets"
REFERENCES = ROOT / "packages/sanji-engine/src/sanji_engine/golden_cases/ziwei/mechanical-trust-references-1.0.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def main() -> int:
    profiles = load(ASSETS / "mechanical-trust-profiles-1.0.0.json")
    evidence = load(ASSETS / "mechanical-source-evidence-1.0.0.json")
    references = load(REFERENCES)
    if profiles["default_profile_id"] is not None:
        raise SystemExit("Ziwei disputed profiles gained a hidden default")
    if profiles["review_status"] != "UNCONFIRMED" or profiles["production_activatable"]:
        raise SystemExit("Ziwei research profile crossed activation gate")
    if any(rule["traditional_source"] is not None for rule in evidence["rules"]):
        raise SystemExit("unreviewed traditional source was silently promoted")
    if references["classification"] != "mechanical_reference":
        raise SystemExit("Ziwei references were mislabeled as authoritative Goldens")
    if references["oracle"]["production_allowed"]:
        raise SystemExit("external Oracle entered production authority")
    print("ziwei mechanical trust validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
