from __future__ import annotations

import json
import subprocess
from pathlib import Path


def execute(value: dict) -> dict:
    runner = Path(__file__).with_name("runner.mjs")
    completed = subprocess.run(
        ["node", str(runner)],
        input=json.dumps(value, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        timeout=30,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "iztro runner failed")
    return json.loads(completed.stdout)


def normalize(raw: dict) -> dict:
    return {
        "life_palace_branch": raw["life_palace_branch"],
        "body_palace_branch": raw["body_palace_branch"],
        "five_element_bureau": raw["five_element_bureau"],
        "palaces": raw["palaces"],
    }
