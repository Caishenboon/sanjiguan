from __future__ import annotations

import json
import os
import subprocess
import shutil
from pathlib import Path


def execute(value: dict) -> dict:
    runtime_dir = Path(
        os.environ.get("SANJI_IZTRO_RUNTIME_DIR", Path(__file__).parent)
    ).resolve()
    runner = runtime_dir / "runner.mjs"
    if not runner.is_file():
        raise RuntimeError("configured iztro runtime does not contain runner.mjs")
    node_binary = os.environ.get("SANJI_NODE_BINARY") or shutil.which("node")
    if not node_binary:
        raise RuntimeError("pinned local Node.js runtime is unavailable")
    completed = subprocess.run(
        [node_binary, str(runner)],
        input=json.dumps(value, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        timeout=30,
        cwd=runtime_dir,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "iztro runner failed")
    return json.loads(completed.stdout)


def normalize(raw: dict) -> dict:
    return {
        "life_palace_branch": raw["life_palace_branch"],
        "body_palace_branch": raw["body_palace_branch"],
        "five_element_bureau": raw["five_element_bureau"],
        "palaces": [
            {key: palace[key] for key in ("index", "name", "branch", "heavenly_stem", "major_stars")}
            for palace in raw["palaces"]
        ],
    }
