import json,sys
from pathlib import Path
from fastapi import FastAPI
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from apps.api.app.research_routes import router
app=FastAPI(title="三际枢 Sprint 2 Research Preview API",version="0.1.0")
app.include_router(router)
target=ROOT/"docs/api/sprint2.openapi.json"
target.write_text(json.dumps(app.openapi(),ensure_ascii=False,indent=2)+"\n","utf-8")
print(target.relative_to(ROOT))
