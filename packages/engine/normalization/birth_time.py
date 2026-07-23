"""Compatibility adapter for the public sanji-engine Calendar contract.

No calendar algorithm may be implemented in this application-facing package.
"""
from __future__ import annotations

from datetime import datetime

from apps.api.app.schemas.models import (
    BirthTimeNormalizationResult,
    OriginalBirthRecord,
)
from sanji_engine import execute


def normalize_birth_time(
    record: OriginalBirthRecord,
    solar_term_instants_utc: list[datetime] | None = None,
) -> BirthTimeNormalizationResult:
    birth_record = record.model_dump(mode="json")
    birth_record["place"]["latitude"] = str(birth_record["place"]["latitude"])
    birth_record["place"]["longitude"] = str(birth_record["place"]["longitude"])
    request = {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": "calendar-compatibility-adapter",
        "run_mode": "research_preview",
        "requested_modules": ["calendar"],
        "input_snapshot": {
            "operation": "normalize_birth_time",
            "birth_record": birth_record,
            "solar_term_instants_utc": [
                value.isoformat() for value in (solar_term_instants_utc or [])
            ],
        },
        "ruleset_bundle_id": "core-boundary-0.1.0",
        "data_versions": {
            "tzdb": "runtime-zoneinfo",
            "ephemeris": "astronomy-engine-2.1.19",
            "calendar_dataset": "calendar-migration-baseline-1.0.0",
        },
        "deterministic_context": {
            "as_of": "2000-01-01T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
    }
    result = execute(request)["module_results"]["calendar"]["result"]
    return BirthTimeNormalizationResult.model_validate(result)
