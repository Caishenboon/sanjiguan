"""Civil-time normalization and astronomical solar-time correction only."""
from __future__ import annotations

import calendar
import math
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _parse_record(record: dict) -> tuple[date, time | None, float]:
    local_date = date.fromisoformat(record["local_date"])
    local_time = time.fromisoformat(record["local_time"]) if record.get("local_time") else None
    longitude = float(record["place"]["longitude"])
    return local_date, local_time, longitude


def _double_hour_bucket(value: datetime) -> int:
    return ((value.hour + 1) % 24) // 2


def _crosses_instant(start: datetime, end: datetime, instant: datetime) -> bool:
    low, high = sorted((start, end))
    return low <= instant.astimezone(timezone.utc) <= high


def equation_of_time_noaa(utc_value: datetime) -> float:
    days = 366 if calendar.isleap(utc_value.year) else 365
    day_of_year = utc_value.timetuple().tm_yday
    fractional_hour = utc_value.hour + utc_value.minute / 60 + utc_value.second / 3600
    gamma = 2 * math.pi / days * (day_of_year - 1 + (fractional_hour - 12) / 24)
    return 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )


def normalize_birth_time(
    record: dict,
    solar_term_instants_utc: list[datetime] | None = None,
) -> dict:
    local_date, local_time, longitude = _parse_record(record)
    warnings: list[str] = []
    prohibited = [
        "不得据此选择命理主盘",
        "不得输出最终日柱或子时换日结论",
        "不得输出旺衰、喜忌或完整大运解释",
    ]
    if local_time is None:
        return {
            "original": record,
            "historical_utc_offset_minutes": None,
            "dst_offset_minutes": None,
            "longitude_correction_minutes": None,
            "equation_of_time_minutes": None,
            "total_apparent_correction_minutes": None,
            "candidates": [{
                "candidate_id": "unknown-time-interval",
                "basis": "unknown_interval",
                "local_datetime": None,
                "utc_datetime": None,
                "method_id": "TIME.UNKNOWN.INTERVAL.V1",
                "is_primary_chart": False,
            }],
            "boundary_difference": {
                "crosses_double_hour_boundary": True,
                "crosses_civil_date_boundary": True,
                "crosses_solar_term_boundary": True,
                "sensitive_rules": ["hour_boundary", "day_boundary", "solar_term_boundary"],
            },
            "correction_chain": [],
            "warnings": ["出生时间未知；只创建候选区间，不伪造具体时刻。"],
            "prohibited_conclusions": prohibited,
        }

    try:
        zone = ZoneInfo(record["timezone_id"])
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown IANA timezone: {record['timezone_id']}") from exc

    civil_naive = datetime.combine(local_date, local_time)
    fold0 = civil_naive.replace(tzinfo=zone, fold=0)
    fold1 = civil_naive.replace(tzinfo=zone, fold=1)
    if fold0.utcoffset() != fold1.utcoffset():
        raise ValueError("local civil time is ambiguous at a timezone transition")
    civil = fold0
    roundtrip = civil.astimezone(timezone.utc).astimezone(zone)
    if roundtrip.replace(tzinfo=None) != civil_naive:
        raise ValueError("local civil time is nonexistent or ambiguous at a timezone transition")

    utc_value = civil.astimezone(timezone.utc)
    utc_offset = civil.utcoffset() or timedelta()
    dst_offset = civil.dst() or timedelta()
    standard_offset = utc_offset - dst_offset
    standard_meridian = standard_offset.total_seconds() / 3600 * 15
    longitude_correction = 4 * (longitude - standard_meridian)
    mean_naive = civil_naive - dst_offset + timedelta(minutes=longitude_correction)
    equation_of_time = equation_of_time_noaa(utc_value)
    apparent_naive = mean_naive + timedelta(minutes=equation_of_time)

    candidates = [
        {
            "candidate_id": "civil-time", "basis": "civil",
            "local_datetime": civil_naive.isoformat(), "utc_datetime": utc_value.isoformat(),
            "method_id": "TIME.CIVIL.IANA.V1", "is_primary_chart": False,
        },
        {
            "candidate_id": "local-mean-solar-time", "basis": "local_mean_solar",
            "local_datetime": mean_naive.isoformat(), "utc_datetime": utc_value.isoformat(),
            "method_id": "TIME.SOLAR.MEAN.USNO.V1", "is_primary_chart": False,
        },
        {
            "candidate_id": "local-apparent-solar-time", "basis": "local_apparent_solar",
            "local_datetime": apparent_naive.isoformat(), "utc_datetime": utc_value.isoformat(),
            "method_id": "TIME.SOLAR.APPARENT.NOAA_FRACTIONAL_YEAR.V1",
            "is_primary_chart": False,
        },
    ]
    term_cross = any(
        _crosses_instant(utc_value, (apparent_naive - civil_naive) + utc_value, instant)
        for instant in (solar_term_instants_utc or [])
    )
    double_hour_cross = _double_hour_bucket(civil_naive) != _double_hour_bucket(apparent_naive)
    date_cross = civil_naive.date() != apparent_naive.date()
    sensitive = []
    if double_hour_cross:
        sensitive.append("hour_boundary")
    if date_cross:
        sensitive.append("day_boundary_method_unconfirmed_D002")
    if term_cross:
        sensitive.append("solar_term_boundary")
    if sensitive:
        warnings.append("校正跨越至少一个候选边界；后续只能进行敏感性分析。")

    return {
        "original": record,
        "historical_utc_offset_minutes": int(utc_offset.total_seconds() // 60),
        "dst_offset_minutes": int(dst_offset.total_seconds() // 60),
        "longitude_correction_minutes": round(longitude_correction, 6),
        "equation_of_time_minutes": round(equation_of_time, 6),
        "total_apparent_correction_minutes": round(
            (apparent_naive - civil_naive).total_seconds() / 60, 6
        ),
        "candidates": candidates,
        "boundary_difference": {
            "crosses_double_hour_boundary": double_hour_cross,
            "crosses_civil_date_boundary": date_cross,
            "crosses_solar_term_boundary": term_cross,
            "sensitive_rules": sensitive,
        },
        "correction_chain": [
            {
                "step": "civil_to_local_mean_solar",
                "input_value": civil_naive.isoformat(),
                "output_value": mean_naive.isoformat(),
                "offset_minutes": round(
                    -dst_offset.total_seconds() / 60 + longitude_correction, 6
                ),
                "source_id": "USNO_EQTIME_AND_IANA_TZDB",
            },
            {
                "step": "local_mean_to_local_apparent_solar",
                "input_value": mean_naive.isoformat(),
                "output_value": apparent_naive.isoformat(),
                "offset_minutes": round(equation_of_time, 6),
                "source_id": "NOAA_GENERAL_SOLAR_POSITION_CALCULATIONS",
            },
        ],
        "warnings": warnings,
        "prohibited_conclusions": prohibited,
    }
