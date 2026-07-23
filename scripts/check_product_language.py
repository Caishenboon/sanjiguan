"""Check user-visible product copy against the frozen terminology contract."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
terms = json.loads((root / "docs/product/terminology.yml").read_text(encoding="utf-8"))
visible_files = list((root / "apps/web/app").rglob("*.tsx"))
visible = "\n".join(path.read_text(encoding="utf-8") for path in visible_files)

errors = []
for word in terms["forbidden_user_terms"]:
    if word in visible:
        errors.append(f"forbidden user-visible term: {word}")
for word in ("三际观", "宿世因缘与命势推演系统", terms["tagline"], "开始观命", "续观三际录"):
    if word not in visible:
        errors.append(f"required home-page term missing: {word}")

report_page = root / "apps/web/app/profile/[id]/report/page.tsx"
if report_page.exists():
    report = report_page.read_text(encoding="utf-8")
    for heading in ("断章", "象名", "象辞", "释义", "应期", "吉凶", "证契", "逆证"):
        if heading not in report:
            errors.append(f"demo report heading missing: {heading}")

if errors:
    raise SystemExit("\n".join(errors))
print("Product language gate passed.")
