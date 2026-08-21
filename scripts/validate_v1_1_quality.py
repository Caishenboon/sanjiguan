"""Static V1.1 quality gate; it performs no network or provider calls."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required = [
        "docs/product/v1-1-comprehensive-red-blue-audit.md",
        "docs/product/v1-1-delivery.md",
        "docs/testing/v1-1-quality.md",
        "docs/user-guide.md",
        "apps/web/app/error.tsx",
        "apps/web/app/loading.tsx",
        "apps/web/app/offline/page.tsx",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit(f"missing V1.1 assets: {', '.join(missing)}")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "tests.test_v1_1_quality", "-v"],
        cwd=ROOT,
        check=False,
    )
    if result.returncode:
        return result.returncode
    print("V1.1 quality contracts passed; no provider call was made")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
