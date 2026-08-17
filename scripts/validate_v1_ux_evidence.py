"""Write or validate the synthetic V1 UX screenshot evidence manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "product" / "evidence" / "screenshots"
MANIFEST_PATH = ROOT / "docs" / "product" / "evidence" / "manifest.json"

EXPECTED = {
    "v1-ux-report-desktop-1440.png": ("/consult/life-trend", 1440, 1000, "三际断章"),
    "v1-ux-life-trend-tablet-768.png": ("/consult/life-trend", 768, 1024, "命势长图"),
    "v1-ux-sushe-wide-1920.png": ("/consult/sushe", 1920, 1080, "宿世星图"),
    "v1-ux-onboarding-mobile-390.png": ("/onboarding", 390, 844, "八步立卷"),
    "v1-ux-insufficient-liuxiang-1440.png": ("/consult/liuxiang", 1440, 1000, "证契未足"),
    "v1-ux-deterministic-report-no-ai-1440.png": ("/consult/life-trend", 1440, 1000, "无 AI 确定性报告"),
    "v1-ux-home-desktop-1440.png": ("/", 1440, 1000, "首页桌面"),
    "v1-ux-home-mobile-390.png": ("/", 390, 844, "首页手机"),
    "v1-ux-onboarding-desktop-1440.png": ("/onboarding", 1440, 1000, "八步立卷桌面"),
    "v1-ux-report-mobile-390.png": ("/consult/life-trend", 390, 844, "断章手机阅读"),
    "v1-ux-zhongyin-1440.png": ("/consult/zhongyin", 1440, 1000, "中阴之门"),
    "v1-ux-yuanqi-1440.png": ("/consult/yuanqi", 1440, 1000, "缘契图"),
    "v1-ux-liuxiang-desktop-1440.png": ("/consult/liuxiang", 1440, 1000, "六象合参"),
    "v1-ux-contested-1440.png": ("/consult/liuxiang", 1440, 1000, "两象相争"),
    "v1-ux-delete-confirmation-1440.png": ("/me/data", 1440, 1000, "删除二次确认"),
    "v1-ux-forbidden-1440.png": ("/forbidden", 1440, 1000, "权限不足"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_manifest() -> dict[str, object]:
    items = []
    for name, (route, width, height, scenario) in sorted(EXPECTED.items()):
        path = EVIDENCE_DIR / name
        if not path.is_file():
            raise SystemExit(f"missing UX evidence: {path.relative_to(ROOT)}")
        items.append(
            {
                "file": f"docs/product/evidence/screenshots/{name}",
                "route": route,
                "viewport": {"width": width, "height": height},
                "scenario": scenario,
                "synthetic_data_only": True,
                "sha256": sha256(path),
            }
        )
    return {
        "schema_version": "sanji-v1-ux-evidence-manifest-1.0",
        "evidence_class": "synthetic_conformance",
        "contains_real_user_data": False,
        "contains_provider_output": False,
        "screenshot_count": len(items),
        "screenshots": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="rewrite the manifest from reviewed screenshots")
    args = parser.parse_args()
    expected = expected_manifest()
    if args.write:
        MANIFEST_PATH.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not MANIFEST_PATH.is_file():
        raise SystemExit("UX evidence manifest is missing; run with --write after visual review")
    actual = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if actual != expected:
        raise SystemExit("UX evidence manifest does not match the reviewed screenshot set")
    print(f"V1 UX evidence validated: {len(EXPECTED)} synthetic screenshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
