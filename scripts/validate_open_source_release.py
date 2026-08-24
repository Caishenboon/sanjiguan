"""Validate the open-source closure without pretending human decisions are complete."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs/open-source/public-release-manifest.json"
REQUIRED_CLOSURE_FILES = {
    "docs/open-source/public-release-authorization-packet.md",
    "docs/open-source/public-switch-runbook.md",
    "docs/open-source/public-release-summary.md",
    "TRADEMARKS.md",
}
TEXT_SUFFIXES = {
    ".css", ".env", ".html", ".js", ".json", ".md", ".mjs", ".py",
    ".sh", ".sql", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml",
}
DISALLOWED_RAW_RESEARCH_SUFFIXES = {".csv", ".parquet", ".feather", ".arrow"}
ABSOLUTE_PATH = re.compile(
    r"(?:[A-Za-z]:[\\/](?:Users|Documents|Temp)[\\/]|/Users/[^/\s]+/|/home/[^/\s]+/)"
)
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "deepseek_value": re.compile(r"(?im)^DEEPSEEK_API_KEY\s*=\s*[^\s<'\"]{8,}\s*$"),
}
SCANNER_SOURCES = {
    "scripts/check_portability.py",
    "scripts/validate_open_source_release.py",
    "scripts/validate_v1_release.py",
}


def _git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    )
    return [line for line in result.stdout.splitlines() if line]


def _tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [value for value in result.stdout.decode("utf-8").split("\0") if value]


def _published_history_authors() -> list[str]:
    authors = _git_lines("log", "--all", "--format=%ae")
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return authors
    parents = _git_lines("rev-list", "--parents", "-n", "1", "HEAD")[0].split()
    if len(parents) <= 2:
        return authors
    synthetic_merge_author = _git_lines("log", "-1", "--format=%ae", "HEAD")[0]
    authors.remove(synthetic_merge_author)
    return authors


def _walk_values(value: object, key: str = "") -> list[tuple[str, object]]:
    values: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for child_key, child in value.items():
            path = f"{key}.{child_key}" if key else child_key
            values.extend(_walk_values(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            values.extend(_walk_values(child, f"{key}[{index}]"))
    else:
        values.append((key, value))
    return values


def audit() -> dict[str, object]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    tracked = _tracked_paths()
    integrity_errors: list[str] = []

    if manifest["schema_version"] != "sanji-open-source-closure/1.0.0":
        integrity_errors.append("manifest_schema_version")

    for relative in REQUIRED_CLOSURE_FILES:
        if not (ROOT / relative).is_file():
            integrity_errors.append(f"missing_publication_control:{relative}")

    controls = manifest.get("prepared_publication_controls", {})
    if controls.get("branch_protection_required_immediately_after_public") is not True:
        integrity_errors.append("branch_protection_not_required")
    if controls.get("private_vulnerability_reporting_required_immediately_after_public") is not True:
        integrity_errors.append("private_vulnerability_reporting_not_required")
    if controls.get("tag_or_release_authorized") is not False:
        integrity_errors.append("tag_or_release_authorized_without_owner")

    for relative in tracked:
        path = ROOT / relative
        if path.suffix.lower() in DISALLOWED_RAW_RESEARCH_SUFFIXES and relative.startswith("research-data/"):
            integrity_errors.append(f"tracked_external_raw_data:{relative}")
        if relative in SCANNER_SOURCES or not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Dockerfile", "Caddyfile"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if ABSOLUTE_PATH.search(text):
            integrity_errors.append(f"absolute_path:{relative}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                integrity_errors.append(f"{label}:{relative}")

    for name in ("vedastro-famous-births.json", "vedastro-marriages.json"):
        dataset = json.loads((ROOT / "research-data/manifests" / name).read_text(encoding="utf-8"))
        if dataset["raw_data_committable"] or dataset["fixture_committable"]:
            integrity_errors.append(f"external_data_committable:{name}")
        if dataset["public_redistribution_allowed"]:
            integrity_errors.append(f"external_redistribution_enabled:{name}")
        if dataset["connector_enabled"]:
            integrity_errors.append(f"public_figure_connector_enabled:{name}")

    dreambank = json.loads(
        (ROOT / "research-data/manifests/dreambank-dreams-en.json").read_text(encoding="utf-8")
    )
    if dreambank["connector_enabled"] or dreambank["raw_data_committable"]:
        integrity_errors.append("dreambank_not_fail_closed")

    sensitive_knowledge_keys = {"content", "full_text", "source_excerpt", "practice_steps"}
    for relative in tracked:
        if not relative.startswith("knowledge/") or not relative.endswith(".json"):
            continue
        value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        for key, child in _walk_values(value):
            if key.rsplit(".", 1)[-1] in sensitive_knowledge_keys and child:
                integrity_errors.append(f"knowledge_fulltext:{relative}:{key}")

    evidence = json.loads((ROOT / "docs/product/evidence/manifest.json").read_text(encoding="utf-8"))
    if evidence["contains_real_user_data"] or evidence["provider_call_count"]:
        integrity_errors.append("product_evidence_not_synthetic")
    if evidence["screenshot_count"] != len(evidence["screenshots"]):
        integrity_errors.append("product_evidence_count")
    for item in evidence["screenshots"]:
        image = ROOT / item["file"]
        if not image.is_file():
            integrity_errors.append(f"missing_screenshot:{item['file']}")
            continue
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        if digest != item["sha256"] or not item["synthetic_data_only"]:
            integrity_errors.append(f"screenshot_manifest_mismatch:{item['file']}")

    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    if "permissions:\n  contents: read" not in workflow:
        integrity_errors.append("workflow_minimum_permissions")
    for permission in ("contents: write", "actions: write", "packages: write", "id-token: write"):
        if permission in workflow:
            integrity_errors.append(f"workflow_write_permission:{permission}")

    project = json.loads((ROOT / "docs/handoff/project-manifest.json").read_text(encoding="utf-8"))
    if len(project["protected_hashes"]) != manifest["repository_state"]["protected_hashes"]:
        integrity_errors.append("protected_hash_count")
    if project["rule_state"] != {
        "activation": "research_active",
        "review_status": "UNCONFIRMED",
        "production_activatable": False,
        "llm_in_core": False,
    }:
        integrity_errors.append("rule_state_changed")

    human_assertions = manifest.get("human_review_assertions", {})
    if human_assertions.get("qualified_traditional_or_lineage_review_claimed") is not False:
        integrity_errors.append("unqualified_traditional_review_claim")
    if human_assertions.get("legal_opinion_claimed") is not False:
        integrity_errors.append("unsupported_legal_opinion_claim")

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    license_activated = "No license is granted" not in license_text
    if license_activated != manifest["license_state"]["project_license_activated"]:
        integrity_errors.append("license_manifest_mismatch")

    authors = _published_history_authors()
    non_noreply = [email for email in authors if not email.endswith("@users.noreply.github.com")]
    if len(non_noreply) != manifest["history_privacy"]["non_noreply_commit_count"]:
        integrity_errors.append("history_email_count_changed")

    blockers = list(manifest["blocking_decisions"])
    public_ready = not integrity_errors and not blockers and license_activated
    return {
        "tracked_files": len(tracked),
        "integrity_errors": sorted(set(integrity_errors)),
        "blocking_decisions": blockers,
        "non_noreply_commit_count": len(non_noreply),
        "public_release_ready": public_ready,
        "safe_to_remain_private": not integrity_errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-public-ready", action="store_true")
    args = parser.parse_args()
    result = audit()
    if result["integrity_errors"]:
        raise SystemExit("\n".join(result["integrity_errors"]))
    if args.require_public_ready and not result["public_release_ready"]:
        raise SystemExit("public release blocked: " + ", ".join(result["blocking_decisions"]))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
