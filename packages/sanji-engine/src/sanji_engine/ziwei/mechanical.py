"""Research-only Zi Wei Dou Shu mechanical chart construction.

No interpretation, auspiciousness, personality, scoring, or LLM behavior is
present here. All method choices are explicit, versioned research profiles.
"""
from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files

from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID

METHOD_ID = "ZIWEI.SANHE.MECHANICAL.RESEARCH.V1"
METHOD_VERSION = "1.0.0"
PROFILE_REGISTRY_VERSION = "ziwei-profile-registry/1.0.0"
TRANSFORMATION_ASSET_VERSION = "birth-year-transformations-candidate/1.0.0"
SOURCE_CLAIM_ASSET_VERSION = "ziwei-source-claim-registry/1.0.0"

STEMS = tuple("甲乙丙丁戊己庚辛壬癸")
BRANCHES = tuple("子丑寅卯辰巳午未申酉戌亥")
PALACE_NAMES = (
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "仆役", "官禄", "田宅", "福德", "父母",
)
NAYIN_ELEMENTS = (
    "金", "火", "木", "土", "金", "火", "水", "土", "金", "木",
    "水", "土", "火", "木", "水", "金", "火", "木", "土", "金",
    "火", "水", "土", "金", "木", "水", "土", "火", "木", "水",
)
BUREAU = {
    "水": {"name": "水二局", "number": 2},
    "木": {"name": "木三局", "number": 3},
    "金": {"name": "金四局", "number": 4},
    "土": {"name": "土五局", "number": 5},
    "火": {"name": "火六局", "number": 6},
}
STAR_OFFSETS = (
    ("紫微", "ziwei", 0), ("天机", "ziwei", -1),
    ("太阳", "ziwei", -3), ("武曲", "ziwei", -4),
    ("天同", "ziwei", -5), ("廉贞", "ziwei", -8),
    ("天府", "tianfu", 0), ("太阴", "tianfu", 1),
    ("贪狼", "tianfu", 2), ("巨门", "tianfu", 3),
    ("天相", "tianfu", 4), ("天梁", "tianfu", 5),
    ("七杀", "tianfu", 6), ("破军", "tianfu", 10),
)


def _asset(name: str) -> dict:
    return json.loads(
        files("sanji_engine").joinpath(f"ziwei/assets/{name}").read_text(encoding="utf-8")
    )


def load_profile(profile_id: str, profile_version: str) -> dict:
    registry = _asset("profiles-1.0.0.json")
    matches = [
        p for p in registry["profiles"]
        if p["profile_id"] == profile_id and p["profile_version"] == profile_version
    ]
    if not matches:
        raise EngineError(INPUT_INVALID, "unknown Ziwei research profile")
    profile = deepcopy(matches[0])
    return {**profile, "content_hash": content_hash(profile)}


def _trace(sequence: int, operation: str, parameters: dict, inputs: list[str], outputs: list[str]) -> dict:
    step = {
        "step_id": f"ziwei:{sequence:04d}:{operation}",
        "sequence": sequence,
        "module_id": "ziwei",
        "operation": operation,
        "input_refs": inputs,
        "rule_refs": [METHOD_ID],
        "source_refs": [
            "ZW-CLAIM-MINGSHEN-001",
            "ZW-CLAIM-WUXINGJU-001",
            "ZW-CLAIM-MAJOR-STARS-001",
            "ZW-CLAIM-SIHUA-001",
            "ZW-CLAIM-DECADE-001",
        ],
        "parameters": parameters,
        "output_refs": outputs,
    }
    return {**step, "calculation_hash": content_hash(step)}


def _cycle_index(stem: str, branch: str) -> int:
    candidates = [index for index in range(60) if index % 10 == STEMS.index(stem)]
    return next(index for index in candidates if index % 12 == BRANCHES.index(branch))


def _palace_stem(year_stem_index: int, branch_index: int) -> str:
    # Five Tigers: the Yin-palace stem starts from the year-stem group.
    yin_starts = (2, 4, 6, 8, 0, 2, 4, 6, 8, 0)
    offset = (branch_index - 2) % 12
    return STEMS[(yin_starts[year_stem_index] + offset) % 10]


def _effective_month(profile: dict, month: int, day: int, leap: bool) -> tuple[int, str]:
    if not leap:
        return month, "ordinary_month"
    if profile["leap_month_policy"] == "same_month_number":
        return month, "leap_same_month"
    if day <= 15:
        return month, "leap_split_first_half_same_month"
    return (month % 12) + 1, "leap_split_second_half_next_month"


def calculate_chart(snapshot: dict) -> tuple[dict, list[dict], dict]:
    if snapshot.get("operation") != "calculate_ziwei_chart":
        raise EngineError(INPUT_INVALID, "Ziwei operation is not supported")
    profile_id = snapshot.get("profile_id")
    profile_version = snapshot.get("profile_version")
    if not isinstance(profile_id, str) or not isinstance(profile_version, str):
        raise EngineError(INPUT_INVALID, "explicit Ziwei profile_id and profile_version are required")
    profile = load_profile(profile_id, profile_version)
    lunar = snapshot.get("lunar_birth")
    if not isinstance(lunar, dict):
        raise EngineError(INPUT_INVALID, "lunar_birth must be an object")
    try:
        year = int(lunar["year"])
        month = int(lunar["month"])
        day = int(lunar["day"])
        leap = lunar["is_leap_month"]
        hour_index = int(lunar["hour_branch_index"])
        traditional_sex = lunar["traditional_sex"]
        target_year = int(snapshot["target_year"])
    except (KeyError, TypeError, ValueError) as exc:
        raise EngineError(INPUT_INVALID, "Ziwei lunar input is incomplete") from exc
    if not (1 <= month <= 12 and 1 <= day <= 30 and 0 <= hour_index <= 11):
        raise EngineError(INPUT_INVALID, "Ziwei lunar month/day/hour index is out of range")
    if not isinstance(leap, bool) or traditional_sex not in {"male", "female"}:
        raise EngineError(INPUT_INVALID, "Ziwei leap flag or traditional sex is invalid")
    provenance = snapshot.get("calendar_provenance")
    if not isinstance(provenance, dict) or provenance.get("conversion_method") != "manual_verified_lunar_input":
        raise EngineError(
            INPUT_INVALID,
            "automatic solar-to-lunar conversion is not frozen; manual verified lunar input is required",
        )
    effective_month, leap_decision = _effective_month(profile, month, day, leap)
    year_stem_index = (year - 4) % 10
    year_branch_index = (year - 4) % 12
    year_ganzhi = STEMS[year_stem_index] + BRANCHES[year_branch_index]
    life_index = (2 + effective_month - 1 - hour_index) % 12
    body_index = (2 + effective_month - 1 + hour_index) % 12
    palace_rows = []
    for sequence, name in enumerate(PALACE_NAMES):
        branch_index = (life_index - sequence) % 12
        stem = _palace_stem(year_stem_index, branch_index)
        palace_rows.append({
            "sequence": sequence,
            "name": name,
            "branch": BRANCHES[branch_index],
            "branch_index": branch_index,
            "heavenly_stem": stem,
            "ganzhi": stem + BRANCHES[branch_index],
            "is_body_palace": branch_index == body_index,
            "major_stars": [],
        })
    life_stem = _palace_stem(year_stem_index, life_index)
    life_cycle = _cycle_index(life_stem, BRANCHES[life_index])
    element = NAYIN_ELEMENTS[life_cycle // 2]
    bureau = BUREAU[element]
    quotient = (day + bureau["number"] - 1) // bureau["number"]
    remainder = quotient * bureau["number"] - day
    position_number = quotient + remainder if remainder % 2 == 0 else quotient - remainder
    ziwei_index = (2 + position_number - 1) % 12
    tianfu_index = (4 - ziwei_index) % 12
    stars = []
    by_branch = {row["branch_index"]: row for row in palace_rows}
    star_order = {item[0]: index for index, item in enumerate(STAR_OFFSETS)}
    for star, system, offset in STAR_OFFSETS:
        origin = ziwei_index if system == "ziwei" else tianfu_index
        branch_index = (origin + offset) % 12
        item = {"name": star, "branch": BRANCHES[branch_index], "branch_index": branch_index}
        stars.append(item)
        by_branch[branch_index]["major_stars"].append(star)
    for row in palace_rows:
        row["major_stars"].sort(key=star_order.__getitem__)
    transforms = _asset("birth-year-transformations-candidate-1.0.0.json")
    source_claims = _asset("source-claims-1.0.0.json")
    transformations = [
        {"label": label, "star": star, "review_status": "UNCONFIRMED"}
        for label, star in zip(transforms["labels"], transforms["table"][STEMS[year_stem_index]])
    ]
    yang_year = year_stem_index % 2 == 0
    forward = (traditional_sex == "male") == yang_year
    decade_cycles = []
    for ordinal in range(12):
        branch_index = (life_index + (ordinal if forward else -ordinal)) % 12
        decade_cycles.append({
            "ordinal": ordinal + 1,
            "start_age": bureau["number"] + ordinal * 10,
            "end_age": bureau["number"] + ordinal * 10 + 9,
            "direction": "forward" if forward else "reverse",
            "branch": BRANCHES[branch_index],
        })
    annual_index = (target_year - 4) % 12
    trace = [
        _trace(100, "accept_verified_lunar_input", {"calendar_provenance": provenance, "lunar_birth": lunar}, ["input:lunar_birth"], ["ziwei:lunar_input"]),
        _trace(200, "apply_leap_month_policy", {"policy": profile["leap_month_policy"], "effective_month": effective_month, "decision": leap_decision}, ["ziwei:lunar_input"], ["ziwei:effective_month"]),
        _trace(300, "resolve_hour_branch", {"hour_branch_index": hour_index, "hour_branch": BRANCHES[hour_index]}, ["input:lunar_birth.hour_branch_index"], ["ziwei:hour_branch"]),
        _trace(400, "locate_life_and_body_palaces", {"life_index": life_index, "body_index": body_index}, ["ziwei:effective_month", "ziwei:hour_branch"], ["ziwei:life_body"]),
        _trace(500, "construct_twelve_palaces", {"palace_order": profile["palace_order"], "year_ganzhi": year_ganzhi}, ["ziwei:life_body"], ["ziwei:twelve_palaces"]),
        _trace(600, "derive_five_element_bureau", {"life_palace_cycle_index": life_cycle, "nayin_element": element, "bureau": bureau}, ["ziwei:twelve_palaces"], ["ziwei:five_element_bureau"]),
        _trace(700, "place_fourteen_major_stars", {"quotient": quotient, "remainder": remainder, "position_number": position_number, "ziwei_index": ziwei_index, "tianfu_index": tianfu_index}, ["ziwei:five_element_bureau", "ziwei:lunar_input"], ["ziwei:major_stars"]),
        _trace(800, "map_birth_year_transformations", {"year_stem": STEMS[year_stem_index], "asset_version": TRANSFORMATION_ASSET_VERSION}, ["ziwei:lunar_input"], ["ziwei:transformations"]),
        _trace(900, "construct_decade_and_annual_foundation", {"direction": "forward" if forward else "reverse", "target_year": target_year, "annual_branch_index": annual_index}, ["ziwei:life_body", "ziwei:five_element_bureau"], ["ziwei:cycles"]),
    ]
    assets = {
        "profiles": PROFILE_REGISTRY_VERSION,
        "transformations": TRANSFORMATION_ASSET_VERSION,
        "source_claims": SOURCE_CLAIM_ASSET_VERSION,
        "nayin": "embedded-mechanical-table/1.0.0",
        "major_stars": "embedded-offset-table/1.0.0",
    }
    result = {
        "module": "ziwei",
        "profile_id": profile_id,
        "profile_version": profile_version,
        "profile_hash": profile["content_hash"],
        "ruleset_status": "research_active",
        "method_status": "traditional_mechanical",
        "review_status": "UNCONFIRMED",
        "production_activatable": False,
        "calendar_input": provenance,
        "lunar_conversion": "not_performed_manual_verified_input",
        "lunar_birth": deepcopy(lunar),
        "leap_month_policy": profile["leap_month_policy"],
        "leap_month_decision": leap_decision,
        "hour_branch": BRANCHES[hour_index],
        "life_palace": {"branch": BRANCHES[life_index], "index": life_index},
        "body_palace": {"branch": BRANCHES[body_index], "index": body_index},
        "twelve_palaces": palace_rows,
        "five_element_bureau": bureau,
        "fourteen_major_stars": stars,
        "approved_auxiliary_stars": [],
        "auxiliary_star_scope_status": "disabled_pending_source_review",
        "birth_year_transformations": transformations,
        "decade_cycles": decade_cycles,
        "annual_position": {"target_year": target_year, "branch": BRANCHES[annual_index], "branch_index": annual_index},
        "boundary_decisions": {"hour": "explicit_branch_index", "leap_month": leap_decision, "automatic_calendar_conversion": "disabled"},
        "assets": assets,
        "interpretation": None,
        "warnings": ["D-005 remains UNCONFIRMED", "This is a research mechanical chart, not a production reading"],
    }
    return result, trace, {
        "ziwei_domain_hash": content_hash(result),
        "profile_hash": profile["content_hash"],
        "asset_hashes": {
            "profiles": content_hash(_asset("profiles-1.0.0.json")),
            "transformations": content_hash(transforms),
            "source_claims": content_hash(source_claims),
        },
    }
