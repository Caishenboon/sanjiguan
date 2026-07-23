import json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class Sprint3ContractTests(unittest.TestCase):
    def test_pwa_cache_excludes_sensitive_routes(self):
        sw=(ROOT/"apps/web/public/sw.js").read_text("utf-8")
        self.assertIn('url.pathname.startsWith("/api/")',sw)
        self.assertIn('url.pathname.startsWith("/profile/")',sw)
        self.assertNotIn('caches.open(CACHE).then(cache=>cache.addAll(["/profile/',sw)

    def test_manifest_and_icons(self):
        manifest=json.loads((ROOT/"apps/web/public/manifest.webmanifest").read_text("utf-8"))
        self.assertEqual("standalone",manifest["display"])
        self.assertEqual("/profile/demo",manifest["start_url"])
        self.assertEqual({"192x192","512x512"},{icon["sizes"] for icon in manifest["icons"]})
        layout=(ROOT/"apps/web/app/layout.tsx").read_text("utf-8")
        registration=(ROOT/"apps/web/components/ServiceWorkerRegistration.tsx").read_text("utf-8")
        self.assertIn("<ServiceWorkerRegistration/>",layout)
        self.assertIn('navigator.serviceWorker.register("/sw.js")',registration)

    def test_owner_research_consent_and_default_template(self):
        route=(ROOT/"apps/api/app/research_routes.py").read_text("utf-8")
        self.assertIn('payload.get("prose_provider","template")',route)
        self.assertIn("research_preview_confirmation_required",route)
        self.assertIn("external_model_confirmation_required",route)
        self.assertIn('user["role"]!="owner"',route)
        self.assertIn("provider.retries=0",route)

    def test_private_research_usage_has_no_raw_content(self):
        migration=(ROOT/"infra/migrations/0010_sprint3_private_research_experience.sql").read_text("utf-8")
        self.assertIn("model_usage_records",migration)
        for forbidden in ("prompt_text","response_text","raw_prompt","raw_response"):
            self.assertNotIn(forbidden,migration)

    def test_production_and_unfrozen_systems_stay_blocked(self):
        manifest=json.loads((ROOT/"packages/rules/v1.0.0/manifest.json").read_text("utf-8"))
        self.assertEqual("draft",manifest["status"])
        self.assertFalse(manifest["production_activatable"])
        pages=" ".join(p.read_text("utf-8") for p in (ROOT/"apps/web/app/profile").rglob("*.tsx"))
        self.assertIn("待命理规则入枢",pages)
        self.assertNotIn("最高修行世",pages)

    def test_core_pages_and_accessibility_alternatives_exist(self):
        expected=["page.tsx","analysis/page.tsx","report/page.tsx","samsara-map/page.tsx",
          "bardo/page.tsx","life-chart/page.tsx","relationships/page.tsx","journal/page.tsx",
          "versions/page.tsx"]
        base=ROOT/"apps/web/app/profile/[id]"
        self.assertTrue(all((base/name).exists() for name in expected))
        star=(base/"samsara-map/page.tsx").read_text("utf-8")
        chart=(base/"life-chart/page.tsx").read_text("utf-8")
        self.assertIn("列表替代视图",star)
        self.assertIn("<table>",chart)
