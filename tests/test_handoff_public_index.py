from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HandoffAndPublicIndexTests(unittest.TestCase):
    def test_manifest_state_is_public_authorized_and_research_only(self):
        manifest = json.loads((ROOT / "docs/handoff/project-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("private_authorized_for_public_switch", manifest["repository"]["visibility"])
        self.assertTrue(manifest["open_source"]["public_release_authorized"])
        self.assertFalse(manifest["rule_state"]["production_activatable"])
        self.assertFalse(manifest["rule_state"]["llm_in_core"])

    def test_home_contains_server_renderable_static_explanation(self):
        source = (ROOT / "apps/web/components/ProductHome.tsx").read_text(encoding="utf-8")
        start = source.index('<section className="public-overview"')
        static_section = source[start:]
        self.assertIn("三际枢负责计算、证据融合与成断", static_section)
        self.assertIn("为什么 AI 不能代替术数计算", static_section)
        self.assertNotIn("session.subject ?", static_section)

    def test_private_routes_are_not_in_sitemap_and_have_headers(self):
        sitemap = (ROOT / "apps/web/app/sitemap.ts").read_text(encoding="utf-8")
        config = (ROOT / "apps/web/next.config.ts").read_text(encoding="utf-8")
        for private in ("/api/", "/admin/", "/me/", "/chronicle", "/results/"):
            self.assertNotIn(private, sitemap)
        self.assertIn("X-Robots-Tag", config)
        self.assertIn("noindex, nofollow, noarchive", config)
        self.assertIn("private, no-store", config)

    def test_llms_files_state_algorithm_boundary(self):
        for name in ("llms.txt", "llms-full.txt"):
            text = (ROOT / "apps/web/public" / name).read_text(encoding="utf-8")
            self.assertIn("DeepSeek", text)
            self.assertIn("Private", text)
            self.assertIn("三际枢", text)

    def test_lighthouse_keeps_public_seo_and_private_quality_budgets_separate(self):
        public = json.loads((ROOT / "apps/web/lighthouserc.json").read_text(encoding="utf-8"))
        private = json.loads((ROOT / "apps/web/lighthouserc.private.json").read_text(encoding="utf-8"))
        public_urls = public["ci"]["collect"]["url"]
        private_urls = private["ci"]["collect"]["url"]
        self.assertEqual(["http://127.0.0.1:3000/"], public_urls)
        self.assertEqual(
            ["http://127.0.0.1:3000/records", "http://127.0.0.1:3000/consult"],
            private_urls,
        )
        self.assertEqual(3, public["ci"]["collect"]["numberOfRuns"])
        self.assertEqual(3, private["ci"]["collect"]["numberOfRuns"])
        self.assertIn("categories:seo", public["ci"]["assert"]["assertions"])
        self.assertNotIn("categories:seo", private["ci"]["assert"]["assertions"])
        for category in ("categories:performance", "categories:accessibility", "categories:best-practices"):
            self.assertEqual(
                public["ci"]["assert"]["assertions"][category],
                private["ci"]["assert"]["assertions"][category],
            )


if __name__ == "__main__":
    unittest.main()
