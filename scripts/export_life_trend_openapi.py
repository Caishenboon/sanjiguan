"""Export Sprint 18 API contract without opening a database."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apps.api.app.life_trend_routes import router

app = FastAPI(
    title="三际观命势长图与三际断章 API",
    version="1.0.0-research",
    description="sanji_original · research_active · UNCONFIRMED · non-production",
)
app.include_router(router)
target = ROOT / "docs/api/life-trend-report.openapi.json"
rendered = json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n"
if target.exists() and "--check" in sys.argv:
    if target.read_text(encoding="utf-8") != rendered:
        raise SystemExit("Life-trend OpenAPI drift; run scripts/export_life_trend_openapi.py")
else:
    target.write_text(rendered, encoding="utf-8")
print(f"Life-trend OpenAPI {'checked' if '--check' in sys.argv else 'exported'}: {target}")
