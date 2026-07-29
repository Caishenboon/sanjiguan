import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProductLanguageTests(unittest.TestCase):
    def test_language_gate(self):
        result = subprocess.run(
            [sys.executable, "scripts/check_product_language.py"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_legacy_demo_report_is_removed_from_ordinary_navigation(self):
        legacy = (ROOT / "apps/web/app/profile/[id]/report/page.tsx").read_text(encoding="utf-8")
        chronicle = (ROOT / "apps/web/components/ChronicleDetail.tsx").read_text(encoding="utf-8")
        self.assertIn('redirect(`/chronicle?subject=', legacy)
        self.assertNotIn("FIXTURE / DEMO", legacy)
        self.assertIn("当时记录了什么", chronicle)
        self.assertIn("当时得到什么结果", chronicle)

    def test_accessibility_contract(self):
        css = (ROOT / "apps/web/app/styles.css").read_text(encoding="utf-8")
        shell = (ROOT / "apps/web/components/ProductShell.tsx").read_text(encoding="utf-8")
        liuxiang = (ROOT / "apps/web/components/LiuxiangReadiness.tsx").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("@media (max-width:", css)
        self.assertIn('aria-label="普通用户主导航"', shell)
        self.assertEqual(5, shell.count("subtitle:"))
        self.assertIn("不显示任何合成测试结果", liuxiang)

    def test_terminology_is_machine_readable(self):
        terms = json.loads((ROOT / "docs/product/terminology.yml").read_text(encoding="utf-8"))
        self.assertEqual("三际观", terms["product_name"])
