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

    def test_demo_report_order_and_label(self):
        text = (ROOT / "apps/web/app/profile/[id]/report/page.tsx").read_text(encoding="utf-8")
        positions = [text.index(word) for word in ("断章", "象名", "象辞", "释义", "应期", "吉凶", "证契", "逆证")]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("FIXTURE / DEMO", text)
        self.assertIn("不代表任何真实推演结果", text)

    def test_accessibility_contract(self):
        css = (ROOT / "apps/web/app/styles.css").read_text(encoding="utf-8")
        home = (ROOT / "apps/web/app/page.tsx").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("@media (max-width:", css)
        self.assertIn('aria-label="主要入口"', home)

    def test_terminology_is_machine_readable(self):
        terms = json.loads((ROOT / "docs/product/terminology.yml").read_text(encoding="utf-8"))
        self.assertEqual("三际观", terms["product_name"])
