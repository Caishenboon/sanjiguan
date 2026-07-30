"""Static V1 release gates; no network and no paid provider calls."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path


root = Path(__file__).resolve().parents[1]
tracked_candidates = []
ignored_dirs = {".git", ".next", "node_modules", ".cache", ".pytest_cache", "coverage", "tmp", "work"}
for current, dirs, files in os.walk(root):
    dirs[:] = [name for name in dirs if name not in ignored_dirs]
    tracked_candidates.extend(Path(current) / name for name in files)
text_suffixes = {".py", ".md", ".json", ".yml", ".yaml", ".sql", ".tsx", ".ts", ".txt", ".toml"}
absolute = re.compile(r"(?:[A-Za-z]:[\\/](?:Users|Documents)[\\/]|/Users/[^/\s]+/|/home/[^/\s]+/)")
for path in tracked_candidates:
    if path == Path(__file__).resolve():
        continue
    if path.suffix.lower() not in text_suffixes and path.name not in {"Dockerfile", "Caddyfile"}:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if absolute.search(text):
        raise SystemExit(f"absolute local path: {path.relative_to(root)}")

compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
api_dockerfile = (root / "apps/api/Dockerfile").read_text(encoding="utf-8")
assert "postgres:16.10-bookworm" in compose
assert "127.0.0.1:3000:3000" in compose
assert "5432:5432" not in compose
assert "service_completed_successfully" in compose
assert "condition: service_healthy" in compose
assert "COPY knowledge /app/knowledge" in api_dockerfile
assert "COPY research-data /app/research-data" in api_dockerfile

env = (root / ".env.example").read_text(encoding="utf-8")
assert "DEEPSEEK_API_KEY=\n" in env
assert "<64_HEX_FROM_SECRET_STORE>" in env
assert "OWNER_BOOTSTRAP_TOKEN=<" in env

for relative in (
    "README.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "docs/deployment/server.md",
    "docs/operations/backup-restore.md",
    "docs/operations/move-computer.md",
    "docs/privacy/data-export-delete.md",
    "docs/releases/v1-checklist.md",
    "sbom.cdx.json",
):
    if not (root / relative).exists():
        raise SystemExit(f"missing release artifact: {relative}")

sbom = json.loads((root / "sbom.cdx.json").read_text(encoding="utf-8"))
assert sbom["bomFormat"] == "CycloneDX"
assert sbom["specVersion"] == "1.6"

workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
assert "v1-release-gates" in workflow
assert "continue-on-error" in workflow  # visual evidence collection pattern
assert "Enforce visual regression result" in workflow
print("V1 release static gates passed")
