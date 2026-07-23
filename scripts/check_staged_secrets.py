"""Scan the exact Git index, including entropy candidates, before commit."""

import math
import re
import subprocess
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1]
git = "git"
raw_names = subprocess.check_output(
    [git, "-c", "core.quotepath=false", "diff", "--cached", "--name-only",
     "--diff-filter=ACMR", "-z"], cwd=root
)
files = [name.decode("utf-8") for name in raw_names.split(b"\0") if name]
excluded_suffixes = {".png", ".jpg", ".ico", ".lock"}
patterns = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "deepseek-value": re.compile(r"(?im)^DEEPSEEK_API_KEY[ \t]*=[ \t]*[^\s\"']{8,}[ \t]*$"),
    "credential-url": re.compile(r"(?i)\b(?:postgres(?:ql)?|https?)://[^/\s:@]+:[^@\s/]+@"),
}
assignment = re.compile(
    r"(?i)(?:secret|token|password|api[_-]?key|private[_-]?key)\s*[:=]\s*[\"']?([A-Za-z0-9+/=_-]{24,})"
)

def entropy(value: str) -> float:
    counts = Counter(value)
    return -sum((count / len(value)) * math.log2(count / len(value)) for count in counts.values())

hits = []
for name in files:
    path = Path(name)
    if path.suffix.lower() in excluded_suffixes or name == "scripts/check_staged_secrets.py":
        continue
    try:
        content = subprocess.check_output(
            [git, "show", f":{name}"], cwd=root, text=True, encoding="utf-8", errors="strict"
        )
    except (subprocess.CalledProcessError, UnicodeDecodeError):
        continue
    scan_content = re.sub(
        r"postgresql://[^\s]*(?:CHANGE_ME|ci-ephemeral-only|\.\.\.)[^\s]*",
        "SAFE_TEST_OR_PLACEHOLDER_URL",
        content,
    )
    for label, pattern in patterns.items():
        if pattern.search(scan_content):
            hits.append(f"{name}: {label}")
    for match in assignment.finditer(scan_content):
        candidate = match.group(1)
        if not re.fullmatch(r"[a-fA-F0-9]{32,}", candidate) and entropy(candidate) >= 4.2:
            hits.append(f"{name}: high-entropy credential assignment")

if hits:
    raise SystemExit("\n".join(sorted(set(hits))))
print(f"Staged secret scan passed: {len(files)} files, no credential patterns or suspicious assignments.")
