"""Export the executable FastAPI contract for drift checks and review."""

import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("STORAGE_BACKEND", "memory")

from apps.api.app.main import app


target = Path("docs/api/openapi.generated.json")
target.write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(target)
