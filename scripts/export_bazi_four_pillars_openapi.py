"""Export the isolated Owner BaZi research adapter contract."""
import json
from pathlib import Path

from fastapi import FastAPI

from apps.api.app.bazi_research_routes import router

app = FastAPI(title="Sanji Owner BaZi Mechanical Research API", version="1.0.0")
app.include_router(router)
target = Path("docs/api/bazi-four-pillars.openapi.json")
target.write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(target)
