"""Export complete traditional research API contracts."""
import json,sys
from pathlib import Path
from fastapi import FastAPI
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from apps.api.app.traditional_complete_routes import router, user_router
app=FastAPI(title="Sanji Traditional Algorithms Complete V1 API",version="1.0.0")
app.include_router(router); app.include_router(user_router)
target=ROOT/"docs/api/traditional-algorithms-complete.openapi.json"
document=json.dumps(app.openapi(),ensure_ascii=False,indent=2)+"\n"
if "--check" in sys.argv:
    if not target.exists() or target.read_text(encoding="utf-8")!=document: raise SystemExit("traditional complete OpenAPI drift")
else: target.write_text(document,encoding="utf-8")
print(target.relative_to(ROOT))
