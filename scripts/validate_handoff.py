"""Validate the handoff manifest, public index surface, and private crawl boundary."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs" / "handoff"
manifest = json.loads((HANDOFF / "project-manifest.json").read_text(encoding="utf-8"))
schema = json.loads((HANDOFF / "project-manifest.schema.json").read_text(encoding="utf-8"))
Draft202012Validator(schema).validate(manifest)

for value in [*manifest["packages"], *manifest["entrypoints"].values(), *manifest["paths"].values(), *manifest["critical_documents"]]:
    if not (ROOT / value).exists():
        raise SystemExit(f"handoff manifest path missing: {value}")

required_handoff = {
    "README.md", "project-history.md", "current-state.md", "system-map.md",
    "next-agent-checklist.md", "decision-boundaries.md", "delivery-index.md",
    "project-manifest.json", "project-manifest.schema.json",
}
if required_handoff - {path.name for path in HANDOFF.iterdir()}:
    raise SystemExit("handoff document set is incomplete")

current = (HANDOFF / "current-state.md").read_text(encoding="utf-8")
for literal in (
    "release: 1.0.0-rc.1", "repository_visibility: private",
    "production_rules_active: false", "llm_in_deterministic_core: false",
    "database_migration_count: 24",
):
    if literal not in current:
        raise SystemExit(f"current-state block missing: {literal}")

home = (ROOT / "apps/web/components/ProductHome.tsx").read_text(encoding="utf-8")
for text in ("三际枢负责计算", "它能看什么", "它如何工作", "为什么 AI 不能代替术数计算", "传统与原创边界", "隐私与数据主权", "开源状态"):
    if text not in home:
        raise SystemExit(f"public home text missing: {text}")
if "useEffect" not in home or "public-overview" not in home:
    raise SystemExit("public static overview or existing private dashboard missing")

sitemap = (ROOT / "apps/web/app/sitemap.ts").read_text(encoding="utf-8")
for private in ("/api/", "/admin/", "/me/", "/profile/", "/chronicle", "/results/"):
    if private in sitemap:
        raise SystemExit(f"private route leaked into sitemap: {private}")

robots = (ROOT / "apps/web/app/robots.ts").read_text(encoding="utf-8")
config = (ROOT / "apps/web/next.config.ts").read_text(encoding="utf-8")
for private in ("/api/:path*", "/admin/:path*", "/me/:path*", "/chronicle/:path*", "/results/:path*"):
    if private not in config:
        raise SystemExit(f"private noindex header missing: {private}")
if "X-Robots-Tag" not in config or "private, no-store" not in config:
    raise SystemExit("private response headers missing")
if "robots.txt 不是权限控制" not in home or "disallow" not in robots:
    raise SystemExit("robots boundary is not explicit")

for llm_file in ("llms.txt", "llms-full.txt"):
    text = (ROOT / "apps/web/public" / llm_file).read_text(encoding="utf-8")
    for required in ("三际枢", "DeepSeek", "Private"):
        if required not in text:
            raise SystemExit(f"{llm_file} missing boundary: {required}")

print(f"Handoff manifest and public/private index boundary passed: {len(manifest['protected_hashes'])} protected hashes.")
