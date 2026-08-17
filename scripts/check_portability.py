"""Reject tracked machine-specific paths and Codex/local database artifacts."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
SCANNER_SOURCES = {SELF, ROOT / "scripts" / "validate_v1_release.py"}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".py", ".ts", ".tsx", ".sql", ".sh", ".env"}
PATTERNS = {
    "windows user path": re.compile(r"[A-Za-z]:[\\/](?:Users|Documents|Temp)[\\/]", re.I),
    "macOS user path": re.compile(r"/Users/[^/\s]+/"),
    "Linux home path": re.compile(r"/home/[^/\s]+/"),
    "Codex attachment path": re.compile(r"[\\/]\.codex[\\/]attachments[\\/]", re.I),
    "local database file": re.compile(r"(?:^|[\\/])[^\s]+\.(?:sqlite3?|db)(?:$|[\s'\"])", re.I | re.M),
}

tracked = subprocess.run(
    ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
).stdout.decode("utf-8").split("\0")
errors: list[str] = []
username = os.environ.get("USERNAME", "").strip()
for relative in filter(None, tracked):
    path = ROOT / relative
    if path.resolve() in SCANNER_SOURCES or not path.is_file():
        continue
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Dockerfile", "Caddyfile", ".env.example"}:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    for label, pattern in PATTERNS.items():
        if pattern.search(text):
            errors.append(f"{relative}: {label}")
    if username and len(username) >= 4 and re.search(rf"(?<![A-Za-z0-9]){re.escape(username)}(?![A-Za-z0-9])", text):
        errors.append(f"{relative}: current Windows username")

if errors:
    raise SystemExit("\n".join(sorted(set(errors))))
print(f"Portability scan passed: {len(tracked)} tracked paths, no machine-specific artifacts.")
