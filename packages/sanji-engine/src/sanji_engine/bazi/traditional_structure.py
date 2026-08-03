"""Versioned, research-only BaZi traditional structural facts.

This module detects table and relation structures only.  It intentionally
does not calculate strength, transformation, pattern, useful gods, luck or
life interpretation.
"""
from __future__ import annotations

from itertools import combinations

from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID

METHOD_ID = "BAZI.TRADITIONAL_STRUCTURE.RESEARCH.V1"
METHOD_VERSION = "1.0.0"
PROFILE_ID = "bazi-traditional-structure-research-v1"
PROFILE_VERSION = "1.0.0"
HIDDEN_STEMS_PROFILE_PRIMARY = "hidden-stems-primary-secondary-residual-candidate-v1"
HIDDEN_STEMS_PROFILE_LUNAR_PYTHON = "hidden-stems-lunar-python-order-comparison-v1"
OPERATION = "calculate_bazi_traditional_structure"
POSITIONS = ("year", "month", "day", "hour")
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

STEM_ELEMENT = dict(zip(STEMS, ("wood", "wood", "fire", "fire", "earth", "earth", "metal", "metal", "water", "water")))
YANG_STEMS = frozenset("甲丙戊庚壬")
GENERATES = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}
CONTROLS = {"wood": "earth", "earth": "water", "water": "fire", "fire": "metal", "metal": "wood"}

# Candidate table retained as ordered structural data.  The labels do not
# imply percentage weights or strength.
HIDDEN_STEMS = {
    "子": (("癸", "primary"),),
    "丑": (("己", "primary"), ("癸", "secondary"), ("辛", "residual")),
    "寅": (("甲", "primary"), ("丙", "secondary"), ("戊", "residual")),
    "卯": (("乙", "primary"),),
    "辰": (("戊", "primary"), ("乙", "secondary"), ("癸", "residual")),
    "巳": (("丙", "primary"), ("戊", "secondary"), ("庚", "residual")),
    "午": (("丁", "primary"), ("己", "secondary")),
    "未": (("己", "primary"), ("丁", "secondary"), ("乙", "residual")),
    "申": (("庚", "primary"), ("壬", "secondary"), ("戊", "residual")),
    "酉": (("辛", "primary"),),
    "戌": (("戊", "primary"), ("辛", "secondary"), ("丁", "residual")),
    "亥": (("壬", "primary"), ("甲", "secondary")),
}
HIDDEN_STEM_PROFILES = {
    HIDDEN_STEMS_PROFILE_PRIMARY: HIDDEN_STEMS,
    HIDDEN_STEMS_PROFILE_LUNAR_PYTHON: {
        **HIDDEN_STEMS,
        "巳": (("丙", "primary"), ("庚", "secondary"), ("戊", "residual")),
    },
}

STEM_COMBINES = {frozenset(pair) for pair in ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")}
BRANCH_PAIRS = {
    "six_harmony": {frozenset(pair) for pair in ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")},
    "six_clash": {frozenset(pair) for pair in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")},
    "six_harm": {frozenset(pair) for pair in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")},
    "six_break": {frozenset(pair) for pair in ("子酉", "丑辰", "寅亥", "卯午", "巳申", "未戌")},
    "mutual_punishment": {frozenset("子卯")},
}
THREE_HARMONIES = tuple(frozenset(value) for value in ("申子辰", "亥卯未", "寅午戌", "巳酉丑"))
THREE_MEETINGS = tuple(frozenset(value) for value in ("亥子丑", "寅卯辰", "巳午未", "申酉戌"))
THREE_PUNISHMENTS = tuple(frozenset(value) for value in ("寅巳申", "丑未戌"))
SELF_PUNISHMENT = frozenset("辰午酉亥")

RELATION_ORDER = {
    name: index for index, name in enumerate((
        "same", "generates", "controls", "five_combine", "six_harmony",
        "six_clash", "six_harm", "six_break", "mutual_punishment",
        "self_punishment", "three_punishment", "three_harmony",
        "three_meeting", "partial_three_harmony", "partial_three_meeting",
    ))
}


def ten_god(day_stem: str, target_stem: str) -> str:
    """Return the mechanical Ten-God relation for a day/target stem pair."""
    if day_stem not in STEMS or target_stem not in STEMS:
        raise EngineError(INPUT_INVALID, "ten-god stems must be canonical heavenly stems")
    day_element, target_element = STEM_ELEMENT[day_stem], STEM_ELEMENT[target_stem]
    same_polarity = (day_stem in YANG_STEMS) == (target_stem in YANG_STEMS)
    if day_element == target_element:
        return "比肩" if same_polarity else "劫财"
    if GENERATES[day_element] == target_element:
        return "食神" if same_polarity else "伤官"
    if GENERATES[target_element] == day_element:
        return "偏印" if same_polarity else "正印"
    if CONTROLS[day_element] == target_element:
        return "偏财" if same_polarity else "正财"
    return "七杀" if same_polarity else "正官"


def _validate_snapshot(snapshot: dict) -> dict[str, dict | None]:
    allowed = {
        "operation", "profile_id", "profile_version", "source_four_pillars",
        "source_candidate_id", "source_ruleset_id", "source_method_id",
        "source_method_version", "month_context", "hidden_stems_profile_id",
    }
    if not isinstance(snapshot, dict) or set(snapshot) - allowed:
        raise EngineError(INPUT_INVALID, "BaZi structure snapshot contains unsupported fields")
    if snapshot.get("operation") != OPERATION:
        raise EngineError(INPUT_INVALID, "BaZi traditional-structure operation is unsupported")
    if snapshot.get("profile_id") != PROFILE_ID or snapshot.get("profile_version") != PROFILE_VERSION:
        raise EngineError(INPUT_INVALID, "explicit supported BaZi structure profile is required")
    if snapshot.get("hidden_stems_profile_id") not in HIDDEN_STEM_PROFILES:
        raise EngineError(INPUT_INVALID, "explicit supported hidden-stems profile is required; no default is permitted")
    pillars = snapshot.get("source_four_pillars")
    if not isinstance(pillars, dict) or set(pillars) != set(POSITIONS):
        raise EngineError(INPUT_INVALID, "source_four_pillars must contain year, month, day and hour")
    normalized = {}
    for position in POSITIONS:
        pillar = pillars[position]
        if pillar is None and position == "hour":
            normalized[position] = None
            continue
        if not isinstance(pillar, dict) or set(pillar) != {"stem", "branch"}:
            raise EngineError(INPUT_INVALID, f"{position} pillar must contain only stem and branch")
        if pillar["stem"] not in STEMS or pillar["branch"] not in BRANCHES:
            raise EngineError(INPUT_INVALID, f"{position} pillar is not canonical")
        normalized[position] = {"stem": pillar["stem"], "branch": pillar["branch"]}
    for field in ("source_candidate_id", "source_ruleset_id", "source_method_id", "source_method_version"):
        if not isinstance(snapshot.get(field), str) or not snapshot[field]:
            raise EngineError(INPUT_INVALID, f"{field} is required for traceability")
    return normalized


def _stem_relations(pillars: dict) -> list[dict]:
    present = [(position, pillars[position]["stem"]) for position in POSITIONS if pillars[position]]
    output = []
    for (left_pos, left), (right_pos, right) in combinations(present, 2):
        relations = []
        if left == right:
            relations.append(("same", "symmetric"))
        left_el, right_el = STEM_ELEMENT[left], STEM_ELEMENT[right]
        if GENERATES[left_el] == right_el:
            relations.append(("generates", "left_to_right"))
        elif GENERATES[right_el] == left_el:
            relations.append(("generates", "right_to_left"))
        if CONTROLS[left_el] == right_el:
            relations.append(("controls", "left_to_right"))
        elif CONTROLS[right_el] == left_el:
            relations.append(("controls", "right_to_left"))
        if frozenset((left, right)) in STEM_COMBINES:
            relations.append(("five_combine", "symmetric"))
        for relation, direction in relations:
            output.append({
                "relation": relation, "direction": direction,
                "participants": [{"position": left_pos, "stem": left}, {"position": right_pos, "stem": right}],
                "completeness": "pair_complete", "transformation_determined": False,
                "consensus_status": "SCHOOL_SPECIFIC" if relation == "five_combine" else "CONSENSUS_MECHANICAL",
            })
    return sorted(output, key=lambda item: (RELATION_ORDER[item["relation"]], tuple(x["position"] for x in item["participants"])))


def _branch_relations(pillars: dict) -> list[dict]:
    present = [(position, pillars[position]["branch"]) for position in POSITIONS if pillars[position]]
    output = []
    for (left_pos, left), (right_pos, right) in combinations(present, 2):
        names = []
        if left == right:
            names.append("same")
            if left in SELF_PUNISHMENT:
                names.append("self_punishment")
        pair = frozenset((left, right))
        for relation, pairs in BRANCH_PAIRS.items():
            if pair in pairs and left != right:
                names.append(relation)
        for group in THREE_HARMONIES:
            if pair <= group and len(pair) == 2:
                names.append("partial_three_harmony")
        for group in THREE_MEETINGS:
            if pair <= group and len(pair) == 2:
                names.append("partial_three_meeting")
        for relation in names:
            output.append({
                "relation": relation,
                "participants": [{"position": left_pos, "branch": left}, {"position": right_pos, "branch": right}],
                "completeness": "partial_candidate" if relation.startswith("partial_") else "pair_complete",
                "formation_determined": False,
                "consensus_status": "DISPUTED" if relation in {"six_break", "mutual_punishment", "self_punishment", "partial_three_harmony", "partial_three_meeting"} else "SCHOOL_SPECIFIC",
            })
    available = {branch for _, branch in present}
    for relation, groups in (("three_punishment", THREE_PUNISHMENTS), ("three_harmony", THREE_HARMONIES), ("three_meeting", THREE_MEETINGS)):
        for group in groups:
            if group <= available:
                participants = [{"position": pos, "branch": branch} for pos, branch in present if branch in group]
                output.append({
                    "relation": relation, "participants": participants,
                    "completeness": "set_complete", "formation_determined": False,
                    "consensus_status": "DISPUTED" if relation == "three_punishment" else "SCHOOL_SPECIFIC",
                })
    return sorted(output, key=lambda item: (RELATION_ORDER[item["relation"]], tuple(x["position"] for x in item["participants"]), tuple(x["branch"] for x in item["participants"])))


def calculate_traditional_structure(snapshot: dict) -> tuple[dict, list[dict], dict]:
    pillars = _validate_snapshot(snapshot)
    hidden_stems_profile_id = snapshot["hidden_stems_profile_id"]
    hidden_stems_table = HIDDEN_STEM_PROFILES[hidden_stems_profile_id]
    day_stem = pillars["day"]["stem"]
    hidden = []
    gods = []
    for position in POSITIONS:
        pillar = pillars[position]
        if pillar is None:
            continue
        gods.append({"position": position, "target_kind": "visible_stem", "target_stem": pillar["stem"], "ten_god": ten_god(day_stem, pillar["stem"])})
        values = []
        for stem, layer in hidden_stems_table[pillar["branch"]]:
            item = {"stem": stem, "layer": layer, "ten_god": ten_god(day_stem, stem)}
            values.append(item)
            gods.append({"position": position, "target_kind": "hidden_stem", "target_stem": stem, "hidden_layer": layer, "ten_god": item["ten_god"]})
        hidden.append({"position": position, "branch": pillar["branch"], "hidden_stems": values})
    month_context = snapshot.get("month_context") if isinstance(snapshot.get("month_context"), dict) else {}
    month_command = {
        "branch": pillars["month"]["branch"],
        "source_position": "month",
        "solar_month_index": month_context.get("solar_month_index"),
        "previous_jie": month_context.get("previous_jie"),
        "next_jie": month_context.get("next_jie"),
        "boundary_sensitive": bool(month_context.get("boundary_sensitive", False)),
        "strength_conclusion": None, "pattern_conclusion": None, "useful_god_conclusion": None,
    }
    result_base = {
        "schema_version": "bazi-traditional-structure-result/1.0.0",
        "method_id": METHOD_ID, "method_version": METHOD_VERSION,
        "profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION,
        "hidden_stems_profile_id": hidden_stems_profile_id,
        "research_status": "research_active", "review_status": "UNCONFIRMED",
        "production_activatable": False, "tradition_scope": "traditional_structure_research",
        "source_four_pillars": {
            "candidate_id": snapshot["source_candidate_id"], "ruleset_id": snapshot["source_ruleset_id"],
            "method_id": snapshot["source_method_id"], "method_version": snapshot["source_method_version"],
            "content_hash": content_hash(pillars),
        },
        "pillars": pillars, "day_master": day_stem, "hidden_stems": hidden,
        "ten_gods": gods, "month_command": month_command,
        "stem_relations": _stem_relations(pillars), "branch_relations": _branch_relations(pillars),
        "missing": ["hour_pillar"] if pillars["hour"] is None else [],
        "disputed_rules": ["si_hidden_stem_order", "branch_break", "punishment_scope", "self_punishment_scope", "partial_combinations"],
        "not_implemented": ["strength", "seasonal_strength", "pattern", "climate_adjustment", "favorable_elements", "useful_god", "luck_cycles", "annual_luck", "transformation", "auspiciousness", "timing"],
        "interpretation": None,
    }
    trace = [
        {"step_id": "bazi-structure:001:validate_source", "sequence": 1, "module_id": "bazi", "operation": "validate_source_four_pillars", "parameters": {"source_ruleset_id": snapshot["source_ruleset_id"], "source_method_version": snapshot["source_method_version"]}, "input_refs": ["input:source_four_pillars"], "output_refs": ["bazi-structure:pillars"]},
        {"step_id": "bazi-structure:002:hidden_stems", "sequence": 2, "module_id": "bazi", "operation": "lookup_hidden_stems", "parameters": {"profile_id": hidden_stems_profile_id, "profile_version": PROFILE_VERSION, "weights_applied": False}, "input_refs": ["bazi-structure:pillars"], "output_refs": ["bazi-structure:hidden_stems"]},
        {"step_id": "bazi-structure:003:ten_gods", "sequence": 3, "module_id": "bazi", "operation": "derive_ten_gods", "parameters": {"day_master": day_stem, "position_changes_relation": False}, "input_refs": ["bazi-structure:pillars", "bazi-structure:hidden_stems"], "output_refs": ["bazi-structure:ten_gods"]},
        {"step_id": "bazi-structure:004:relations", "sequence": 4, "module_id": "bazi", "operation": "detect_structural_relations", "parameters": {"transformation_determined": False, "formation_determined": False}, "input_refs": ["bazi-structure:pillars"], "output_refs": ["bazi-structure:stem_relations", "bazi-structure:branch_relations"]},
    ]
    result = {**result_base, "result_hash": content_hash(result_base)}
    return result, trace, {"bazi_structure_domain_hash": result["result_hash"]}
