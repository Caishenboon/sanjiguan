import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V11QualityContracts(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_web_requests_have_timeout_cancellation_and_request_id(self):
        source = self.read("apps/web/lib/product-session.ts")
        self.assertIn("timeoutMs", source)
        self.assertIn("AbortController", source)
        self.assertIn('"X-Request-ID"', source)
        self.assertIn('cache: "no-store"', source)
        self.assertIn("关联ID", source)

    def test_proxy_returns_safe_backward_compatible_errors(self):
        source = self.read("apps/web/app/api/[...path]/route.ts")
        self.assertIn("api_origin_not_configured", source)
        self.assertIn("upstream_unavailable", source)
        self.assertIn('"Cache-Control": "no-store"', source)
        self.assertIn("request_id", source)
        self.assertIn("requestIdPattern", source)

    def test_security_headers_and_normalized_request_ids(self):
        next_config = self.read("apps/web/next.config.ts")
        api = self.read("apps/api/app/postgres_app.py")
        security = self.read("apps/api/app/core/security.py")
        for header in ("Content-Security-Policy", "Permissions-Policy", "Referrer-Policy", "X-Frame-Options"):
            self.assertIn(header, next_config)
        self.assertIn("normalized_request_id", api)
        self.assertIn("REQUEST_ID_PATTERN", security)
        self.assertNotIn("request_body", api)

    def test_api_error_envelope_preserves_structured_detail(self):
        api = self.read("apps/api/app/postgres_app.py")
        self.assertIn("detail=exc.detail", api)
        self.assertIn('exc.detail.get("code") if isinstance(exc.detail, dict)', api)

    def test_pwa_keeps_private_data_out_of_cache(self):
        source = self.read("apps/web/public/sw.js")
        for private_path in ("/api/", "/profile/", "/chronicle", "/records", "/consult", "/me", "prompt"):
            self.assertIn(private_path, source)
        self.assertIn("/offline", source)
        self.assertIn("caches.delete", source)
        self.assertIn("return;", source)

    def test_global_states_and_fixed_mobile_navigation_exist(self):
        shell = self.read("apps/web/components/ProductShell.tsx")
        self.assertTrue((ROOT / "apps/web/app/error.tsx").is_file())
        self.assertTrue((ROOT / "apps/web/app/loading.tsx").is_file())
        self.assertTrue((ROOT / "apps/web/app/offline/page.tsx").is_file())
        for label in ("首页", "三际录", "合参", "断章", "更多"):
            self.assertIn(label, shell)


if __name__ == "__main__":
    unittest.main()
