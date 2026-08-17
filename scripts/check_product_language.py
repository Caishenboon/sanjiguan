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
    "建立三际录", "记录一件事", "开始一次合参",
):
    if word not in visible:
        errors.append(f"required home-page term missing: {word}")

language = (root / "apps/web/lib/product-language.ts").read_text(encoding="utf-8")
for technical, product_copy in (
    ("strength", "象势"), ("confidence", "证契完备度"),
    ("decisive", "象成，可断"), ("provisional", "象初成，仍待补证"),
    ("contested", "两象相争"), ("insufficient", "证契未足，不成断"),
    ("counterevidence", "逆证"), ("missingness", "尚缺资料"),
    ("boundary_sensitivity", "边界敏感"), ("profile dispute", "规则方案存在分歧"),
    ("replay", "复演"), ("reanalyze", "重观"),
):
    if technical not in language or product_copy not in language:
        errors.append(f"product dictionary mapping missing: {technical} -> {product_copy}")

if errors:
    raise SystemExit("\n".join(errors))

# Ordinary-user surfaces must not expose raw connection errors or revive retired names.
ordinary = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (root / "apps/web/components").glob("*.tsx")
)
for forbidden in ("api_origin_not_configured", "三际镜", "AI算前世", "AI 算前世"):
    if forbidden in ordinary:
        raise SystemExit(f"forbidden ordinary-surface copy: {forbidden}")
for required in ("方法与版本", "象势", "证契完备度", "六象合参", "宿世星图", "中阴之门", "缘契图"):
    if required not in ordinary:
        raise SystemExit(f"required V1 product language missing: {required}")

print("Product language gate passed.")
