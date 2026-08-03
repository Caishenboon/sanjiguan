"""Optional, paid-provider smoke. Never runs without an explicit opt-in."""
from __future__ import annotations

import os
import subprocess
import sys


if os.getenv("SANJI_ALLOW_PAID_SMOKE") != "YES":
    raise SystemExit("set SANJI_ALLOW_PAID_SMOKE=YES to explicitly authorize one synthetic smoke")
if not os.getenv("DEEPSEEK_API_KEY"):
    raise SystemExit("DEEPSEEK_API_KEY is not configured")
subprocess.run(
    [sys.executable, "scripts/run_deepseek_research_smoke.py"],
    check=True,
)
