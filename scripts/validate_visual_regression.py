"""Prevent visual regression determinism controls from silently weakening."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
config = (ROOT / "apps/web/playwright.config.ts").read_text(encoding="utf-8")
package = (ROOT / "apps/web/package.json").read_text(encoding="utf-8")
layout = (ROOT / "apps/web/app/layout.tsx").read_text(encoding="utf-8")
spec = (ROOT / "apps/web/tests/visual/flagship.spec.ts").read_text(encoding="utf-8")
contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

required_workflow = (
    "web-visual-determinism:",
    "runs-on: ubuntu-24.04",
    "os: windows-2025",
    "snapshot_platform: linux",
    "snapshot_platform: win32",
    "id: visual_regression",
    "continue-on-error: true",
    "actions/upload-artifact@v6",
    "visual-regression-${{ matrix.snapshot_platform }}-${{ github.run_id }}",
    "steps.visual_regression.outcome == 'failure'",
    "Enforce visual regression result",
)
required_config = (
    "__screenshots__/{platform}/{projectName}",
    "maxDiffPixelRatio: 0.012",
    'timezoneId: "UTC"',
)
font_packages = (
    "@fontsource/noto-sans-sc",
    "@fontsource/noto-serif-sc",
    "@fontsource/noto-sans-mono",
)

errors: list[str] = []
for needle in required_workflow:
    if needle not in workflow:
        errors.append(f"CI visual determinism control missing: {needle}")
for needle in required_config:
    if needle not in config:
        errors.append(f"Playwright determinism control missing: {needle}")
for package_name in font_packages:
    if package_name not in package or package_name not in layout:
        errors.append(f"pinned local font is not installed and imported: {package_name}")
if "document.fonts.check" not in spec or "document.fonts.ready" not in spec:
    errors.append("visual tests do not fail closed when deterministic fonts are unavailable")
if "innerHTML" in spec:
    errors.append("visual tests must exercise rendered application states, not injected HTML")
for platform in ("linux", "win32"):
    snapshots = tuple(
        (ROOT / "apps/web/tests/visual/__screenshots__" / platform).rglob("*.png")
    )
    if len(snapshots) != 21:
        errors.append(
            f"{platform} must contain exactly 21 reviewed visual baselines; "
            f"found {len(snapshots)}"
        )
if "不得通过提高像素差异阈值" not in contributing:
    errors.append("contribution policy does not forbid threshold inflation")

if errors:
    raise SystemExit("\n".join(errors))
print("Visual regression determinism controls passed.")
