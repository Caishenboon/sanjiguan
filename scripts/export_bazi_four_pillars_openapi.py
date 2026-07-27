"""Export the isolated Owner BaZi research adapter contract."""
import json
import sys
from pathlib import Path

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.bazi_research_routes import router

app = FastAPI(title="Sanji Owner BaZi Mechanical Research API", version="1.0.0")
app.include_router(router)
target = ROOT / "docs/api/bazi-four-pillars.openapi.json"
target.write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(target.relative_to(ROOT))
