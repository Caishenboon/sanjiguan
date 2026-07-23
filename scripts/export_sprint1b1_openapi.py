"""Export the Sprint 1B-1 router contract without opening a database connection."""
import json
import sys
from pathlib import Path

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evidence_routes import router

app = FastAPI(title="三际观 Sprint 1B-1 Evidence API", version="0.1.0")
app.include_router(router)
target = ROOT / "docs/api/sprint1b1.openapi.json"
target.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", "utf-8")
print(target.relative_to(ROOT))
