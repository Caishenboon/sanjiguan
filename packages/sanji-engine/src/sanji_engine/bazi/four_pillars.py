"""Deterministic, research-only mechanical four-pillar calculation.

This module deliberately contains no interpretation, scoring, auspiciousness,
Ten Gods, strength, luck-cycle, past-life, relationship, or LLM behavior.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from zoneinfo import ZoneInfo

from ..calendar import normalize_birth_time, solar_term_instant
from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID
from .profiles import day_epoch_asset, execution_profile_registry, load_execution_profile

METHOD_ID = "BAZI.FOUR_PILLARS.MECHANICAL.RESEARCH.V1"
METHOD_VERSION = "1.0.0"
CALENDAR_METHOD_VERSION = "CALENDAR.MIGRATION.BASELINE.V1"
SOLAR_TERM_DATA_VERSION = "astronomy-engine/2.1.19"
BOUNDARY_CASE_ASSET_VERSION = "bazi-boundary-cases/1.0.0"

STEMS = tuple("甲乙丙丁戊己庚辛壬癸")
BRANCHES = tuple("子丑寅卯辰巳午未申酉戌亥")
JIE = (
    (285, "小寒", 1, 2, 11),
    (315, "立春", 2, 1, 0),
    (345, "惊蛰", 3, 2, 1),
    (15, "清明", 4, 1, 2),
    (45, "立夏", 5, 2, 3),
    (75, "芒种", 6, 2, 4),
    (105, "小暑", 7, 3, 5),
    (135, "立秋", 8, 3, 6),
    (165, "白露", 9, 3, 7),
    (195, "寒露", 10, 4, 8),
    (225, "立冬", 11, 3, 9),
    (255, "大雪", 12, 3, 10),
)
UNKNOWN_INTERVALS = (
    ("early_zi", "00:00:00", "01:00:00"),
    ("chou", "01:00:00", "03:00:00"),
    ("yin", "03:00:00", "05:00:00"),
    ("mao", "05:00:00", "07:00:00"),
    ("chen", "07:00:00", "09:00:00"),
    ("si", "09:00:00", "11:00:00"),
    ("wu", "11:00:00", "13:00:00"),
    ("wei", "13:00:00", "15:00:00"),
    ("shen", "15:00:00", "17:00:00"),
    ("you", "17:00:00", "19:00:00"),
    ("xu", "19:00:00", "21:00:00"),
    ("hai", "21:00:00", "23:00:00"),
    ("late_zi", "23:00:00", "24:00:00"),
)


def _jdn_gregorian(value: date) -> int:
    """Fliegel/Van Flandern-style integer Gregorian JDN, independent of OS locale."""
    a = (14 - value.month) // 12
    y = value.year + 4800 - a
    m = value.month + 12 * a - 3
    return (
        value.day + (153 * m + 2) // 5 + 365 * y + y // 4
        - y // 100 + y // 400 - 32045
    )


def _pillar(cycle_index: int) -> dict:
    normalized = cycle_index % 60
    stem_index = normalized % 10
    branch_index = normalized % 12
    return {
        "stem": STEMS[stem_index],
        "branch": BRANCHES[branch_index],
        "ganzhi": STEMS[stem_index] + BRANCHES[branch_index],
        "stem_index": stem_index,
        "branch_index": branch_index,
        "cycle_index": normalized,
    }


def _day_index(value: date) -> tuple[int, int]:
    epoch = day_epoch_asset()
    serial = _jdn_gregorian(value)
    anchor = _jdn_gregorian(date.fromisoformat(epoch["anchor_date"]))
    return (epoch["anchor_cycle_index"] + serial - anchor) % 60, serial


@lru_cache(maxsize=512)
def _jie_for_year(year: int) -> tuple[tuple, ...]:
    result = []
    for longitude, name, month, approximate_day, month_index in JIE:
        start = datetime(year, month, approximate_day, tzinfo=timezone.utc) - timedelta(days=4)
        instant = solar_term_instant(longitude, start, 10)
        result.append((instant, longitude, name, month_index))
    return tuple(sorted(result))


def _surrounding_jie(instant_utc: datetime) -> tuple[tuple, tuple]:
    items = [
        item for year in range(instant_utc.year - 1, instant_utc.year + 2)
        for item in _jie_for_year(year)
    ]
    items.sort()
    prior = [item for item in items if item[0] <= instant_utc]
    following = [item for item in items if item[0] > instant_utc]
    if not prior or not following:
        raise EngineError(INPUT_INVALID, "solar-term boundary could not be bracketed")
    return prior[-1], following[0]


def _surrounding_jie_wall(
    wall_time: datetime, timezone_id: str
) -> tuple[tuple, tuple]:
    zone = ZoneInfo(timezone_id)
    items = [
        (item[0].astimezone(zone).replace(tzinfo=None), *item)
        for year in range(wall_time.year - 1, wall_time.year + 2)
        for item in _jie_for_year(year)
    ]
    items.sort()
    prior = [item for item in items if item[0] <= wall_time]
    following = [item for item in items if item[0] > wall_time]
    if not prior or not following:
        raise EngineError(INPUT_INVALID, "solar-term wall-time boundary could not be bracketed")
    # Return the original (instant, longitude, name, month_index) tuple.
    return prior[-1][1:], following[0][1:]


def _lichun(year: int) -> datetime:
    return next(item[0] for item in _jie_for_year(year) if item[1] == 315)


@lru_cache(maxsize=1)
def _boundary_asset_hash() -> str:
    from .conformance import load_boundary_cases

    return load_boundary_cases()["content_hash"]


def _time_basis(normalized: dict, basis: str) -> datetime:
    by_basis = {item["basis"]: item for item in normalized["candidates"]}
    item = by_basis.get(basis)
    if not item or not item["local_datetime"]:
        raise EngineError(INPUT_INVALID, f"calendar did not produce required time basis: {basis}")
    return datetime.fromisoformat(item["local_datetime"])


def _trace(sequence: int, operation: str, parameters: dict, inputs: list[str], outputs: list[str]) -> dict:
    step = {
        "step_id": f"bazi:{sequence:04d}:{operation}",
        "sequence": sequence,
        "module_id": "bazi",
        "operation": operation,
        "input_refs": inputs,
        "rule_refs": [METHOD_ID],
        "source_refs": [
            "HKO_HEAVENLY_STEMS_EARTHLY_BRANCHES_TABLES",
            "HKO_24_SOLAR_TERMS_LONGITUDES",
            "USNO_JULIAN_DATE_INTEGER_CALENDAR_CONVERSION",
            "BAZI_DAY_EPOCH_RESEARCH_ASSET_UNCONFIRMED",
        ],
        "parameters": parameters,
        "output_refs": outputs,
    }
    return {**step, "calculation_hash": content_hash(step)}


def _track_result(
    record: dict,
    normalized: dict,
    utc_instant: datetime,
    track: dict,
    candidate_id: str,
    interval: dict | None,
    sequence_base: int,
) -> tuple[dict, list[dict]]:
    pillar_times = {
        pillar: _time_basis(normalized, basis)
        for pillar, basis in track["pillar_time_basis"].items()
    }
    basis_time = pillar_times["day"]
    year_time = pillar_times["year"]
    month_time = pillar_times["month"]
    hour_time = pillar_times["hour"]
    zone = ZoneInfo(record["timezone_id"])
    lichun = _lichun(year_time.year)
    lichun_wall = lichun.astimezone(zone).replace(tzinfo=None)
    pillar_year = year_time.year if year_time >= lichun_wall else year_time.year - 1
    year_index = (pillar_year - 1984) % 60
    year_pillar = _pillar(year_index)
    prior_jie, next_jie = _surrounding_jie_wall(month_time, record["timezone_id"])
    civil_time = _time_basis(normalized, "civil")
    civil_lichun = _lichun(civil_time.year)
    civil_lichun_wall = civil_lichun.astimezone(zone).replace(tzinfo=None)
    civil_pillar_year = (
        civil_time.year if civil_time >= civil_lichun_wall else civil_time.year - 1
    )
    civil_prior_jie, _ = _surrounding_jie_wall(civil_time, record["timezone_id"])
    month_index = prior_jie[3]
    month_stem = ((year_pillar["stem_index"] % 5) * 2 + 2 + month_index) % 10
    month_pillar = {
        **_pillar(0),
        "stem": STEMS[month_stem],
        "branch": BRANCHES[(month_index + 2) % 12],
        "ganzhi": STEMS[month_stem] + BRANCHES[(month_index + 2) % 12],
        "stem_index": month_stem,
        "branch_index": (month_index + 2) % 12,
        "cycle_index": next(
            index for index in range(60)
            if index % 10 == month_stem and index % 12 == (month_index + 2) % 12
        ),
    }
    effective_date = basis_time.date()
    crossed_rollover = False
    if track["day_rollover"] == "zichu_23" and basis_time.hour >= 23:
        effective_date += timedelta(days=1)
        crossed_rollover = True
    day_index, day_serial = _day_index(effective_date)
    day_pillar = _pillar(day_index)
    hour_branch = ((hour_time.hour + 1) % 24) // 2
    hour_stem_date = effective_date
    if (
        track["hour_stem_day_policy"] == "next_day_for_late_zi"
        and hour_time.hour >= 23
    ):
        hour_stem_date = hour_time.date() + timedelta(days=1)
    hour_day_index, _ = _day_index(hour_stem_date)
    hour_stem = ((hour_day_index % 10) * 2 + hour_branch) % 10
    hour_pillar = {
        **_pillar(0),
        "stem": STEMS[hour_stem],
        "branch": BRANCHES[hour_branch],
        "ganzhi": STEMS[hour_stem] + BRANCHES[hour_branch],
        "stem_index": hour_stem,
        "branch_index": hour_branch,
        "cycle_index": next(
            index for index in range(60)
            if index % 10 == hour_stem and index % 12 == hour_branch
        ),
    }
    correction = normalized["total_apparent_correction_minutes"]
    result = {
        "candidate_id": candidate_id,
        "track_id": track["track_id"],
        "time_basis": track["time_basis"],
        "used_local_datetime": basis_time.isoformat(),
        "used_times_by_pillar": {
            pillar: value.isoformat() for pillar, value in pillar_times.items()
        },
        "utc_instant": utc_instant.isoformat(),
        "unknown_time_interval": interval,
        "pillars": {
            "year": {
                **year_pillar,
                "boundary_policy": "lichun_astronomical_instant",
                "boundary_instant_utc": lichun.isoformat(),
                "boundary_wall_datetime": lichun_wall.isoformat(),
                "comparison_basis": track["pillar_time_basis"]["year"],
                "comparison": "at_or_after" if year_time >= lichun_wall else "before",
            },
            "month": {
                **month_pillar,
                "solar_month_index": month_index,
                "previous_jie": {
                    "name": prior_jie[2], "longitude": prior_jie[1],
                    "instant_utc": prior_jie[0].isoformat(),
                    "wall_datetime": prior_jie[0].astimezone(zone).replace(
                        tzinfo=None
                    ).isoformat(),
                },
                "next_jie": {
                    "name": next_jie[2], "longitude": next_jie[1],
                    "instant_utc": next_jie[0].isoformat(),
                    "wall_datetime": next_jie[0].astimezone(zone).replace(
                        tzinfo=None
                    ).isoformat(),
                },
                "comparison_basis": track["pillar_time_basis"]["month"],
                "derivation": "year_stem_group_then_yin_month_offset",
            },
            "day": {
                **day_pillar,
                "day_serial_jdn": day_serial,
                "effective_date": effective_date.isoformat(),
                "day_epoch_version": "bazi-day-epoch/1.0.0",
                "rollover_policy": track["day_rollover"],
                "rollover_applied": crossed_rollover,
            },
            "hour": {
                **hour_pillar,
                "double_hour_index": hour_branch,
                "boundary_policy": "23-01_then_two_hour_start_inclusive",
                "hour_stem_day": hour_stem_date.isoformat(),
                "derivation": "day_stem_group_then_zi_hour_offset",
            },
        },
        "boundary_flags": {
            "calendar_crosses_double_hour": normalized["boundary_difference"][
                "crosses_double_hour_boundary"
            ],
            "calendar_crosses_civil_date": normalized["boundary_difference"][
                "crosses_civil_date_boundary"
            ],
            "day_rollover_applied": crossed_rollover,
            "at_year_boundary": year_time == lichun_wall,
            "at_month_boundary": (
                month_time
                == prior_jie[0].astimezone(zone).replace(tzinfo=None)
            ),
            "solar_correction_crosses_year_boundary": civil_pillar_year != pillar_year,
            "solar_correction_crosses_month_boundary": civil_prior_jie[3] != month_index,
        },
        "correction_minutes": {
            "longitude": f'{normalized["longitude_correction_minutes"]:.6f}',
            "equation_of_time": f'{normalized["equation_of_time_minutes"]:.6f}',
            "total_apparent": f"{correction:.6f}",
        },
        "time_calculation_chain": {
            "user_local_civil": f"{record['local_date']}T{record['local_time']}",
            "historical_utc_offset_minutes": normalized["historical_utc_offset_minutes"],
            "dst_offset_minutes": normalized["dst_offset_minutes"],
            "utc_instant": utc_instant.isoformat(),
            "local_mean_solar": next(
                item["local_datetime"] for item in normalized["candidates"]
                if item["basis"] == "local_mean_solar"
            ),
            "local_apparent_solar": next(
                item["local_datetime"] for item in normalized["candidates"]
                if item["basis"] == "local_apparent_solar"
            ),
            "selected_by_pillar": {
                pillar: {
                    "basis": track["pillar_time_basis"][pillar],
                    "datetime": value.isoformat(),
                }
                for pillar, value in pillar_times.items()
            },
            "correction_steps": [
                {
                    **{key: value for key, value in step.items() if key != "offset_minutes"},
                    "offset_minutes": f'{step["offset_minutes"]:.6f}',
                }
                for step in normalized["correction_chain"]
            ],
        },
    }
    trace = [
        _trace(sequence_base + 10, "normalize_historical_civil_time", {
            "timezone_id": record["timezone_id"],
            "utc_offset_minutes": normalized["historical_utc_offset_minutes"],
            "dst_offset_minutes": normalized["dst_offset_minutes"],
            "utc_instant": utc_instant.isoformat(),
        }, ["input:birth_record"], [f"bazi:{candidate_id}:utc"]),
        _trace(sequence_base + 20, "select_profile_time_basis", {
            "track": track, "used_local_datetime": basis_time.isoformat(),
            "correction_minutes": result["correction_minutes"],
        }, [f"bazi:{candidate_id}:utc"], [f"bazi:{candidate_id}:time_basis"]),
        _trace(sequence_base + 30, "derive_year_pillar", result["pillars"]["year"],
               [f"bazi:{candidate_id}:utc"], [f"bazi:{candidate_id}:year"]),
        _trace(sequence_base + 40, "derive_month_pillar", result["pillars"]["month"],
               [f"bazi:{candidate_id}:year"], [f"bazi:{candidate_id}:month"]),
        _trace(sequence_base + 50, "derive_day_pillar", result["pillars"]["day"],
               [f"bazi:{candidate_id}:time_basis"], [f"bazi:{candidate_id}:day"]),
        _trace(sequence_base + 60, "derive_hour_pillar", result["pillars"]["hour"],
               [f"bazi:{candidate_id}:day"], [f"bazi:{candidate_id}:hour"]),
    ]
    return result, trace


def _normalize(record: dict) -> dict:
    try:
        normalized = normalize_birth_time(record)
    except (KeyError, TypeError, ValueError) as exc:
        raise EngineError(INPUT_INVALID, f"invalid birth record: {exc}") from exc
    return normalized


def _validate_record(record: dict) -> None:
    required = {
        "local_date", "local_time", "calendar_type", "time_precision",
        "timezone_id", "place", "user_confirmed",
    }
    missing = sorted(required - set(record))
    if missing:
        raise EngineError(INPUT_INVALID, "birth record is incomplete", {"fields": missing})
    if record["calendar_type"] != "gregorian":
        raise EngineError(INPUT_INVALID, "only explicit Gregorian input is supported")
    if not isinstance(record["place"], dict) or not {
        "latitude", "longitude", "name", "precision"
    } <= set(record["place"]):
        raise EngineError(INPUT_INVALID, "birth place and coordinate precision are required")
    for field, lower, upper in (
        ("latitude", Decimal("-90"), Decimal("90")),
        ("longitude", Decimal("-180"), Decimal("180")),
    ):
        raw = record["place"].get(field)
        if not isinstance(raw, str):
            raise EngineError(
                INPUT_INVALID,
                f"{field} must be an explicitly scaled decimal string",
            )
        try:
            coordinate = Decimal(raw)
        except InvalidOperation as exc:
            raise EngineError(INPUT_INVALID, f"{field} is invalid") from exc
        if not coordinate.is_finite() or not lower <= coordinate <= upper:
            raise EngineError(INPUT_INVALID, f"{field} is outside its valid range")
    try:
        year = date.fromisoformat(record["local_date"]).year
    except (TypeError, ValueError) as exc:
        raise EngineError(INPUT_INVALID, "local_date is invalid") from exc
    if year < 1900 or year > 2099:
        raise EngineError(INPUT_INVALID, "research calendar window is 1900 through 2099")
    if record["local_time"] is not None:
        try:
            time.fromisoformat(record["local_time"])
        except (TypeError, ValueError) as exc:
            raise EngineError(INPUT_INVALID, "local_time is invalid") from exc
    if record["time_precision"] not in {
        "second", "minute", "hour", "double_hour", "half_day", "unknown"
    }:
        raise EngineError(INPUT_INVALID, "time_precision is not supported")


def calculate_four_pillars(snapshot: dict) -> tuple[dict, list[dict], dict]:
    allowed = {
        "operation", "profile_id", "profile_version", "birth_record",
        "input_provenance",
    }
    unexpected = sorted(set(snapshot) - allowed)
    if unexpected:
        raise EngineError(INPUT_INVALID, "unsupported BaZi input fields", {"fields": unexpected})
    if snapshot.get("operation") != "calculate_bazi_four_pillars":
        raise EngineError(INPUT_INVALID, "BaZi operation is not supported")
    profile = load_execution_profile(
        snapshot.get("profile_id"), snapshot.get("profile_version")
    )
    record = deepcopy(snapshot.get("birth_record"))
    if not isinstance(record, dict):
        raise EngineError(INPUT_INVALID, "birth_record must be an object")
    _validate_record(record)
    candidates: list[dict] = []
    trace: list[dict] = []
    missing_data: list[str] = []
    insufficient_time = (
        record["local_time"] is None
        or record["time_precision"] in {"unknown", "hour", "double_hour", "half_day"}
    )
    if insufficient_time:
        missing_data.append(
            "birth_time" if record["local_time"] is None else "birth_time_exact"
        )
        for interval_index, (name, start, end) in enumerate(UNKNOWN_INTERVALS):
            candidate_record = deepcopy(record)
            candidate_record["local_time"] = start
            candidate_record["time_precision"] = "candidate_interval"
            normalized = _normalize(candidate_record)
            utc_instant = datetime.fromisoformat(
                next(item["utc_datetime"] for item in normalized["candidates"]
                     if item["basis"] == "civil")
            )
            interval = {
                "interval_id": name,
                "start_local_inclusive": start,
                "end_local_exclusive": end,
                "source": "enumerated_not_user_supplied",
            }
            for track_index, track in enumerate(profile["time_tracks"]):
                candidate, steps = _track_result(
                    candidate_record, normalized, utc_instant, track,
                    f"{interval_index:02d}-{track['track_id']}", interval,
                    1000 + interval_index * 100 + track_index * 10000,
                )
                candidates.append(candidate)
                trace.extend(steps)
    else:
        normalized = _normalize(record)
        utc_instant = datetime.fromisoformat(
            next(item["utc_datetime"] for item in normalized["candidates"]
                 if item["basis"] == "civil")
        )
        for track_index, track in enumerate(profile["time_tracks"]):
            candidate, steps = _track_result(
                record, normalized, utc_instant, track, track["track_id"], None,
                1000 + track_index * 10000,
            )
            candidates.append(candidate)
            trace.extend(steps)
    candidates.sort(key=lambda item: (item["candidate_id"], item["track_id"]))
    raw_candidate_count = len(candidates)
    deduplicated: list[dict] = []
    by_key: dict[tuple, dict] = {}
    for candidate in candidates:
        interval_id = (
            candidate["unknown_time_interval"]["interval_id"]
            if candidate["unknown_time_interval"] else None
        )
        key = (
            interval_id,
            *(
                candidate["pillars"][pillar]["ganzhi"]
                for pillar in ("year", "month", "day", "hour")
            ),
        )
        track_summary = {
            "candidate_id": candidate["candidate_id"],
            "track_id": candidate["track_id"],
            "time_basis": candidate["time_basis"],
            "used_times_by_pillar": candidate["used_times_by_pillar"],
            "boundary_flags": candidate["boundary_flags"],
            "correction_minutes": candidate["correction_minutes"],
            "time_calculation_chain": candidate["time_calculation_chain"],
        }
        if key in by_key:
            by_key[key]["equivalent_tracks"].append(track_summary)
            continue
        unique = deepcopy(candidate)
        unique["equivalent_tracks"] = [track_summary]
        by_key[key] = unique
        deduplicated.append(unique)
    candidates = deduplicated
    registry = execution_profile_registry()
    epoch = day_epoch_asset()
    boundary_hash = _boundary_asset_hash()
    unique_pillars = {
        tuple(candidate["pillars"][name]["ganzhi"] for name in ("year", "month", "day", "hour"))
        for candidate in candidates
    }
    result = {
        "module": "bazi",
        "method_id": METHOD_ID,
        "method_version": METHOD_VERSION,
        "method_class": "traditional_mechanical_research_candidate",
        "research_status": "research_active",
        "review_status": "UNCONFIRMED",
        "production_activatable": False,
        "profile": profile,
        "input_provenance": deepcopy(snapshot.get("input_provenance", {})),
        "calendar_version": CALENDAR_METHOD_VERSION,
        "solar_term_data_version": SOLAR_TERM_DATA_VERSION,
        "day_epoch": epoch,
        "boundary_case_asset_version": BOUNDARY_CASE_ASSET_VERSION,
        "boundary_case_asset_hash": boundary_hash,
        "candidate_count": len(candidates),
        "raw_candidate_count": raw_candidate_count,
        "candidate_limit": 26,
        "candidates": candidates,
        "four_pillars": candidates[0]["pillars"] if len(candidates) == 1 else None,
        "profile_difference": len(unique_pillars) > 1,
        "missing_data": missing_data,
        "data_completeness": "partial_unknown_time" if missing_data else "complete_input",
        "candidate_truncated": False,
        "truncation_reason": None,
        "deduplication": {
            "key": "unknown_interval_plus_four_pillar_ganzhi",
            "raw_count": raw_candidate_count,
            "unique_count": len(candidates),
            "merged_count": raw_candidate_count - len(candidates),
            "distinct_method_tracks_preserved_as": "equivalent_tracks",
        },
        "selection": "explicit_profile_no_primary_chart",
        "interpretation": None,
        "auspiciousness": None,
        "manifestation_period": None,
    }
    domain_hash = content_hash(result)
    return result, trace, {
        "bazi_domain_hash": domain_hash,
        "profile_registry_hash": registry["content_hash"],
        "profile_hash": profile["content_hash"],
        "day_epoch_hash": epoch["content_hash"],
        "boundary_case_asset_version": BOUNDARY_CASE_ASSET_VERSION,
        "boundary_case_asset_hash": boundary_hash,
        "calendar_method_version": CALENDAR_METHOD_VERSION,
        "solar_term_data_version": SOLAR_TERM_DATA_VERSION,
    }
