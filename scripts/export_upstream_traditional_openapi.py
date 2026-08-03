"""Export the isolated owner-only pinned-upstream research contract."""
import json
import sys
from pathlib import Path
from fastapi import FastAPI

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from apps.api.app.upstream_traditional_routes import router

app=FastAPI(title="Sanji Pinned Upstream Traditional Research API",version="1.0.0")
app.include_router(router)
target=ROOT/"docs/api/upstream-traditional.openapi.json"
target.write_text(json.dumps(app.openapi(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(target.relative_to(ROOT))
