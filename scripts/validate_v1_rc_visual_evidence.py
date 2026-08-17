"""Validate the committed V1 RC screenshots without image-library dependencies."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/releases/evidence/v1-rc-visual-evidence.json"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
REQUIRED_SCENARIOS = {
    "desktop_life_trend_and_sanji_report",
    "tablet_life_trend",
    "wide_past_life_candidate_with_epistemic_state",
    "mobile_synthetic_subject_onboarding",
    "insufficient_no_verdict",
    "deterministic_report_without_deepseek",
}


def png_size(payload: bytes) -> tuple[int, int]:
    if payload[:8] != PNG_SIGNATURE or payload[12:16] != b"IHDR":
        raise SystemExit("visual evidence is not a valid PNG")
    return struct.unpack(">II", payload[16:24])


data = json.loads(MANIFEST.read_text(encoding="utf-8"))
assert data["schema_version"] == "sanji-visual-evidence/1.0"
assert data["release"] == "1.0.0-rc.1"
assert data["data_class"] == "synthetic_only"
assert data["provider_policy"] == "no_external_provider"
screenshots = data["screenshots"]
assert len(screenshots) >= 6
assert {item["scenario"] for item in screenshots} == REQUIRED_SCENARIOS

for item in screenshots:
    relative = Path(item["file"])
    if relative.is_absolute() or ".." in relative.parts:
        raise SystemExit(f"unsafe visual evidence path: {relative}")
    path = ROOT / relative
    payload = path.read_bytes()
    width, height = png_size(payload)
    assert (width, height) == (item["width"], item["height"]), item
    assert hashlib.sha256(payload).hexdigest() == item["sha256"], item
    assert item["provider_calls"] == 0
    assert item["reviewed"] is True

print(f"V1 RC visual evidence passed: {len(screenshots)} synthetic screenshots")
