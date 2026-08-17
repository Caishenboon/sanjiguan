"""Check local Markdown links and the shape of external evidence links."""
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
errors = []
external = set()
checked_local = 0

documents = list((ROOT / "docs").rglob("*.md"))
documents.extend(path for path in (ROOT / "README.md", ROOT / "README.zh-CN.md", ROOT / "AGENTS.md") if path.exists())
for document in documents:
    text = document.read_text(encoding="utf-8")
    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
        if target.startswith("#"):
            continue
        parsed = urlparse(target)
        if parsed.scheme in {"http", "https"}:
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"{document.relative_to(ROOT)}: unsafe/malformed external link: {target}")
            else:
                external.add(target)
            continue
        if parsed.scheme:
            errors.append(f"{document.relative_to(ROOT)}: unsupported link scheme: {target}")
            continue
        local = (document.parent / unquote(parsed.path)).resolve()
        try:
            local.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{document.relative_to(ROOT)}: link escapes repository: {target}")
            continue
        checked_local += 1
        if not local.exists():
            errors.append(f"{document.relative_to(ROOT)}: missing local target: {target}")

if errors:
    print(*errors, sep="\n")
    sys.exit(1)
print(f"Documentation links passed: {checked_local} local, {len(external)} unique HTTPS evidence links.")
