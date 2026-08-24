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
    if path in {
        Path(__file__).resolve(),
        (root / "scripts/check_portability.py").resolve(),
        (root / "scripts/validate_open_source_release.py").resolve(),
    }:
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
assert "networks: [private, ingress]" in compose
assert "ingress:" in compose
assert "PUBLIC_ORIGIN: ${PUBLIC_ORIGIN:-http://127.0.0.1:3000}" in compose
demo = (root / "scripts/demo.py").read_text(encoding="utf-8")
assert 'life_trend["deterministic_report_hash"]' in demo
restore_rehearsal = (root / "scripts/ci_restore_rehearsal.sh").read_text(encoding="utf-8")
assert 'test "$stable_checks" -ge 3' in restore_rehearsal
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
    "README.zh-CN.md",
    "LICENSE",
    "NOTICE",
    "CODE_OF_CONDUCT.md",
    "SUPPORT.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "docs/deployment/server.md",
    "docs/operations/backup-restore.md",
    "docs/operations/move-computer.md",
    "docs/privacy/data-export-delete.md",
    "docs/releases/v1-checklist.md",
    "docs/open-source/license-audit-v1-rc.md",
    "docs/open-source/knowledge-boundary-v1-rc.md",
    "docs/open-source/public-release-closure-v1.md",
    "docs/open-source/public-release-manifest.json",
    "docs/open-source/publication-decisions.md",
    "docs/releases/v1-rc-delivery.md",
    "docs/releases/v1-rc-security-audit.md",
    "docs/releases/v1-rc-final-red-blue-review.md",
    "AGENTS.md",
    "docs/handoff/project-manifest.json",
    "docs/handoff/project-manifest.schema.json",
    "docs/handoff/current-state.md",
    "docs/setup/new-machine-windows.md",
    "docs/setup/new-machine-linux.md",
    "apps/web/public/llms.txt",
    "apps/web/public/llms-full.txt",
    "docs/releases/evidence/v1-rc-cold-start.redacted.txt",
    "docs/releases/evidence/v1-rc-backup-restore.redacted.txt",
    "docs/releases/evidence/v1-rc-test-summary.json",
    "docs/releases/evidence/v1-rc-visual-evidence.json",
    "docs/releases/evidence/screenshots/README.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/pull_request_template.md",
    "sbom.cdx.json",
):
    if not (root / relative).exists():
        raise SystemExit(f"missing release artifact: {relative}")

release_delivery = (root / "docs/releases/v1-rc-delivery.md").read_text(encoding="utf-8")
test_summary = json.loads((root / "docs/releases/evidence/v1-rc-test-summary.json").read_text(encoding="utf-8"))
for stale in ("remote_ci=pending", "run_url=null", "完成后补入"):
    if stale in release_delivery:
        raise SystemExit(f"stale release evidence marker: {stale}")
assert test_summary["remote_ci"]["status"] == "success"
assert test_summary["remote_ci"]["run_id"] == 31998530992
assert test_summary["remote_ci"]["jobs_passed"] == 6
assert test_summary["remote_ci"]["jobs_failed"] == 0
assert test_summary["remote_ci"]["jobs_skipped"] == 0
assert test_summary["remote_ci"]["soft_failures"] == 0
assert len(test_summary["historical_failed_runs"]) == 2
assert test_summary["repository_state"] == {
    "visibility": "private",
    "pull_request": 26,
    "pull_request_state": "open",
    "mergeable_state": "ready_to_merge",
    "tags": 0,
    "releases": 0,
}
assert test_summary["release_decisions"] == {
    "ENGINEERING_RC_READY": True,
    "AI_HANDOFF_READY": True,
    "NEW_MACHINE_HANDOFF_READY": True,
    "MERGE_READY": True,
    "OPEN_SOURCE_READY": False,
    "PUBLIC_RELEASE_AUTHORIZED": False,
}

sbom = json.loads((root / "sbom.cdx.json").read_text(encoding="utf-8"))
assert sbom["bomFormat"] == "CycloneDX"
assert sbom["specVersion"] == "1.6"
assert sbom["metadata"]["component"]["version"] == "1.0.0-rc.1"

license_notice = (root / "LICENSE").read_text(encoding="utf-8")
assert "No license is granted" in license_notice
assert "AGPL-3.0-or-later" in license_notice and "CC BY-SA 4.0" in license_notice

workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
assert "v1-release-gates" in workflow
assert "continue-on-error" in workflow  # visual evidence collection pattern
assert "Enforce visual regression result" in workflow

subject_setup = (root / "apps/web/components/SubjectSetup.tsx").read_text(encoding="utf-8")
coin_journey = (root / "apps/web/components/ThreeCoinJourney.tsx").read_text(encoding="utf-8")
assert 'latitude: 0, longitude: 0' not in subject_setup
assert 'coordinate_source: "user_confirmed"' in subject_setup
assert 'Array.from({length:6},()=>["","",""])' in coin_journey
assert '<option value="">请选择</option>' in coin_journey
handoff_manifest = json.loads((root / "docs/handoff/project-manifest.json").read_text(encoding="utf-8"))
assert handoff_manifest["release"] == "1.0.0-rc.1"
assert handoff_manifest["repository"]["visibility"] == "private"
assert handoff_manifest["open_source"]["public_release_authorized"] is False
assert handoff_manifest["rule_state"]["production_activatable"] is False
assert len(handoff_manifest["protected_hashes"]) >= 10
assert (root / "infra/migrations/0022_v1_rc_original_birth_record.sql").exists()
assert (root / "infra/migrations/0023_v1_rc_traditional_member_rls.sql").exists()
assert (root / "infra/migrations/0024_v1_rc_invitation_issuance.sql").exists()
pwa_manifest = json.loads((root / "apps/web/public/manifest.webmanifest").read_text(encoding="utf-8"))
assert pwa_manifest["start_url"] == "/start"
service_worker = (root / "apps/web/public/sw.js").read_text(encoding="utf-8")
for prefix in ("/api/", "/profile/", "/chronicle", "/records", "/consult", "/me"):
    assert f'url.pathname.startsWith("{prefix}")' in service_worker
print("V1 release static gates passed")
