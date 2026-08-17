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
    for label in ("六象合参", "三际断章", "宿世星图", "中阴之门", "命势长图", "缘契图", "观照录", "历次命卷", "设置与数据管理"):
        assert label in shell, f"desktop feature navigation missing: {label}"
    assert "product-mobile-nav" in shell and "DESKTOP_FEATURES.map" in shell

    liuxiang = read("apps/web/components/LiuxiangReadiness.tsx")
    for required in ("真实映射规则尚未通过审校", "不显示任何合成测试结果", "<VerdictBanner status={run.status}>"):
        assert required in liuxiang, f"liuxiang boundary missing: {required}"
    for forbidden in ("sprint3-fixture", "synthetic_conformance", "aggregate_hash"):
        assert forbidden not in liuxiang, f"synthetic research output leaked to ordinary liuxiang page: {forbidden}"

    session = read("apps/web/lib/product-session.ts")
    assert "sessionStorage" in session and "localStorage" not in session
    assert "Idempotency-Key" in session

    language = read("apps/web/lib/product-language.ts")
    required_terms = {
        "strength": "象势",
        "confidence": "证契完备度",
        "decisive": "象成，可断",
        "provisional": "象初成，仍待补证",
        "contested": "两象相争",
        "insufficient": "证契未足，不成断",
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
