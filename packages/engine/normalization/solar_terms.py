"""Compatibility adapter for the public sanji-engine Calendar contract."""
from __future__ import annotations

from datetime import datetime

from sanji_engine import execute

SOLAR_TERM_LONGITUDES = tuple(range(0, 360, 15))


def solar_term_instant(
    target_longitude: int,
    start_utc: datetime,
    limit_days: float = 20,
) -> datetime:
    request = {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": "calendar-solar-term-compatibility-adapter",
        "run_mode": "research_preview",
        "requested_modules": ["calendar"],
        "input_snapshot": {
            "operation": "solar_term_instant",
            "target_longitude": target_longitude,
            "search_start_utc": start_utc.isoformat(),
            "limit_days": str(limit_days),
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
    value = execute(request)["module_results"]["calendar"]["result"]["instant_utc"]
    return datetime.fromisoformat(value)
