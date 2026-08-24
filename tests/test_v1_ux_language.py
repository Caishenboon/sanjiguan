import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V1UxLanguageContractTests(unittest.TestCase):
    def test_mobile_navigation_has_exactly_five_user_destinations(self):
        shell = (ROOT / "apps/web/components/ProductShell.tsx").read_text("utf-8")
        mobile = shell.split("const MOBILE_NAV", 1)[1].split("] as const", 1)[0]
        for label in ("首页", "三际录", "合参", "断章", "更多"):
            self.assertIn(f'label: "{label}"', mobile)
        self.assertEqual(5, mobile.count("{ label:"))

    def test_result_language_separates_strength_and_evidence_completeness(self):
        shell = (ROOT / "apps/web/components/ProductShell.tsx").read_text("utf-8")
        self.assertIn("现有证契指向该象的力度", shell)
        self.assertIn("独立资料的完整、稳定与少冲突程度", shell)
        self.assertNotIn("象势强度 {", shell)

    def test_current_user_surfaces_have_no_retired_brand_or_raw_api_error(self):
        visible = "\n".join(
            path.read_text("utf-8")
            for folder in (ROOT / "apps/web/app", ROOT / "apps/web/components")
            for path in folder.rglob("*.tsx")
        )
        self.assertNotIn("三际镜", visible)
        self.assertNotIn("api_origin_not_configured", visible)
        self.assertNotIn("AI算前世", visible)

    def test_safety_and_research_state_are_not_softened(self):
        visible = "\n".join(
            path.read_text("utf-8") for path in (ROOT / "apps/web/components").glob("*.tsx")
        )
        for phrase in ("研究态", "未经审校", "不预测死亡", "不是历史身份认定"):
            self.assertIn(phrase, visible)

    def test_report_and_trend_have_text_equivalents(self):
        report = (ROOT / "apps/web/components/LifeTrendResearch.tsx").read_text("utf-8")
        self.assertIn("命势长图文字表格回退", report)
        self.assertIn("命势长图移动端文字列表", report)
        self.assertIn("确定性模板成文", report)
        self.assertIn("role=\"img\"", report)

    def test_destructive_action_has_secondary_confirmation(self):
        settings = (ROOT / "apps/web/components/DataSettings.tsx").read_text("utf-8")
        self.assertIn('role="dialog"', settings)
        self.assertIn('aria-modal="true"', settings)
        self.assertIn("确认彻底删除", settings)


if __name__ == "__main__":
    unittest.main()
