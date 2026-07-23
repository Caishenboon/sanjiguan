"""Astronomical solar-longitude instants; no BaZi interpretation."""
from __future__ import annotations

from datetime import datetime, timezone

import astronomy

SOLAR_TERM_LONGITUDES = tuple(range(0, 360, 15))


def solar_term_instant(target_longitude: int, start_utc: datetime, limit_days: float = 20) -> datetime:
    if target_longitude not in SOLAR_TERM_LONGITUDES:
        raise ValueError("target_longitude must be a multiple of 15 in [0, 345]")
    if start_utc.tzinfo is None:
        raise ValueError("start_utc must be timezone-aware")
    normalized = start_utc.astimezone(timezone.utc)
    astro_start = astronomy.Time.Make(
        normalized.year,
        normalized.month,
        normalized.day,
        normalized.hour,
        normalized.minute,
        normalized.second + normalized.microsecond / 1_000_000,
    )
    result = astronomy.SearchSunLongitude(float(target_longitude), astro_start, limit_days)
    if result is None:
        raise ValueError("solar longitude not found in search window")
    return result.Utc().replace(tzinfo=timezone.utc)
