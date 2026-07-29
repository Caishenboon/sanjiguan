"""Check user-visible product copy against the frozen terminology contract."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
terms = json.loads((root / "docs/product/terminology.yml").read_text(encoding="utf-8"))
visible_files = list((root / "apps/web/app").rglob("*.tsx")) + list(
    (root / "apps/web/components").rglob("*.tsx")
)
visible = "\n".join(path.read_text(encoding="utf-8") for path in visible_files)

errors = []
for word in terms["forbidden_user_terms"]:
    if word in visible:
        errors.append(f"forbidden user-visible term: {word}")
for word in (
    "三际观", "宿世因缘与命势推演系统", terms["tagline"],
    "完善我的资料", "记录一件事", "开始一次合参",
):
    if word not in visible:
        errors.append(f"required home-page term missing: {word}")

language = (root / "apps/web/lib/product-language.ts").read_text(encoding="utf-8")
for technical, product_copy in (
    ("strength", "象势强度"), ("confidence", "证据可信度"),
    ("decisive", "象意较明"), ("provisional", "初见其象"),
    ("contested", "诸象相争"), ("insufficient", "资料不足，暂不成断"),
    ("counterevidence", "逆证"), ("missingness", "尚缺资料"),
    ("boundary_sensitivity", "边界敏感"), ("profile dispute", "规则方案存在分歧"),
    ("replay", "按原版本重放"), ("reanalyze", "用当前版本重新分析"),
):
    if technical not in language or product_copy not in language:
        errors.append(f"product dictionary mapping missing: {technical} -> {product_copy}")

if errors:
    raise SystemExit("\n".join(errors))
print("Product language gate passed.")
