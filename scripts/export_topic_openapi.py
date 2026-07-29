"""Export Sprint 17 topic API without opening a database."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.topic_routes import router

app = FastAPI(
    title="三际观宿世观、中阴观与缘契观 API",
    version="1.0.0-research",
    description="sanji_original · research_active · UNCONFIRMED · non-production",
)
app.include_router(router)
target = ROOT / "docs/api/topic-engines.openapi.json"
rendered = json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n"
if target.exists() and "--check" in sys.argv:
    if target.read_text(encoding="utf-8") != rendered:
        raise SystemExit("Topic OpenAPI drift; run scripts/export_topic_openapi.py")
else:
    target.write_text(rendered, encoding="utf-8")
print(f"Topic OpenAPI {'checked' if '--check' in sys.argv else 'exported'}: {target}")
