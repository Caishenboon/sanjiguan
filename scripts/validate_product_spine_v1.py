"""Static gates for the ordinary-user product spine.

This validates UI boundaries only. It does not validate divination theory.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    shell = read("apps/web/components/ProductShell.tsx")
    nav_labels = ['label: "首页"', 'label: "记录"', 'label: "合参"', 'label: "三际录"', 'label: "我的"']
    assert all(label in shell for label in nav_labels), "five ordinary navigation labels required"
    assert shell.count("subtitle:") == 5, "ordinary primary navigation must contain exactly five entries"

    liuxiang = read("apps/web/components/LiuxiangReadiness.tsx")
    for required in ("资料不足，暂不成断", "真实映射规则尚未通过审校", "不显示任何合成测试结果"):
        assert required in liuxiang, f"liuxiang boundary missing: {required}"
    for forbidden in ("sprint3-fixture", "synthetic_conformance", "aggregate_hash"):
        assert forbidden not in liuxiang, f"synthetic research output leaked to ordinary liuxiang page: {forbidden}"

    session = read("apps/web/lib/product-session.ts")
    assert "sessionStorage" in session and "localStorage" not in session
    assert "Idempotency-Key" in session

    language = read("apps/web/lib/product-language.ts")
    required_terms = {
        "strength": "象势强度",
        "confidence": "证据可信度",
        "decisive": "象意较明",
        "provisional": "初见其象",
        "contested": "诸象相争",
        "insufficient": "资料不足，暂不成断",
    }
    for technical, label in required_terms.items():
        assert technical in language and label in language

    proxy = read("apps/web/proxy.ts")
    assert 'matcher: ["/admin/:path*"]' in proxy
    assert '"/forbidden"' in proxy
    assert 'fetch(new URL("/api/v1/me", apiOrigin)' in proxy
    assert "sanjiguan-role" not in proxy

    ordinary_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            WEB / "components" / "ProductHome.tsx",
            WEB / "components" / "ConsultCenter.tsx",
            WEB / "components" / "LiuxiangReadiness.tsx",
        ]
    )
    for forbidden in ("sprint3-fixture", "sixImages", "candidate_id", "independence_group"):
        assert forbidden not in ordinary_sources, f"research implementation detail leaked: {forbidden}"

    print("product-spine-v1: routes, language, permissions, and synthetic-output gates passed")


if __name__ == "__main__":
    main()
