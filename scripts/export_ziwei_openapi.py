"""Export the isolated Owner Ziwei research and Oracle differential contract."""
import json
import sys
from pathlib import Path

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.ziwei_research_routes import router

app = FastAPI(title="Sanji Owner Ziwei Mechanical Research API", version="1.0.0")
app.include_router(router)
target = ROOT / "docs/api/ziwei-research.openapi.json"
target.write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(target.relative_to(ROOT))
