"""Repository secret scan for committed source; complements CI gitleaks."""

import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
excluded = {
    "work", "node_modules", ".next", ".git", ".cache", "outputs", "__pycache__",
    "test-results", "playwright-report", ".lighthouseci", "storybook-static",
    "dist", "build", "coverage", ".venv", "venv",
}
patterns = [
    re.compile(r"(?im)^(deepseek_api_key)[ \t]*=[ \t]*[^\s\"']{8,}[ \t]*$"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
hits = []
for path in root.rglob("*"):
    if not path.is_file() or any(part in excluded for part in path.parts):
        continue
    if path.name == "check_secrets.py" or path.suffix.lower() in {".png", ".jpg", ".ico", ".lock"}:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for pattern in patterns:
        if pattern.search(text):
            hits.append(f"{path.relative_to(root)}: {pattern.pattern}")
if hits:
    raise SystemExit("\n".join(hits))
print("Secret scan passed: no credential-shaped values found.")
