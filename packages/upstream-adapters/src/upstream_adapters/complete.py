"""Deterministic research profiles built only from pinned upstream facts.

The functions in this module are adapters, not claims of cross-school
consensus.  Every non-mechanical decision is exposed in the returned trace.
"""
from __future__ import annotations

from collections import Counter


STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
STEM_ELEMENT = dict(zip(STEMS, ("wood", "wood", "fire", "fire", "earth", "earth", "metal", "metal", "water", "water")))
BRANCH_ELEMENT = dict(zip(BRANCHES, ("water", "earth", "wood", "wood", "earth", "fire", "fire", "earth", "metal", "metal", "earth", "water")))
GENERATES = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}
CONTROLS = {"wood": "earth", "earth": "water", "water": "fire", "fire": "metal", "metal": "wood"}
TEN_GOD_SUPPORT = {"比肩", "劫财", "正印", "偏印"}
TEN_GOD_OUTPUT = {"食神", "伤官", "正财", "偏财", "正官", "七杀"}


def bazi_complete(structure: dict, day_master: str, fortune_cycles: dict | None) -> dict:
    """Apply the pinned, reviewable Zi-ping research profile.

    This deliberately uses evidence counts and ratios rather than opaque
    weights.  Month command, visible support and roots are separate facts.
    """
    visible = [item["ten_god_stem"] for item in structure.values()]
    hidden = [god for item in structure.values() for god in item["ten_gods_hidden"]]
    month = structure["month"]
    month_primary = month["ten_gods_hidden"][0]
    support_facts = [f"visible:{i}" for i, god in enumerate(visible) if god in TEN_GOD_SUPPORT]
    support_facts += [f"hidden:{i}" for i, god in enumerate(hidden) if god in TEN_GOD_SUPPORT]
    drain_facts = [f"visible:{i}" for i, god in enumerate(visible) if god in TEN_GOD_OUTPUT]
    drain_facts += [f"hidden:{i}" for i, god in enumerate(hidden) if god in TEN_GOD_OUTPUT]
    roots = [position for position, item in structure.items()
             if item["ten_gods_hidden"] and item["ten_gods_hidden"][0] in {"比肩", "劫财"}]
    month_supports = month_primary in TEN_GOD_SUPPORT
    support_units = len(support_facts) + len(roots) + (2 if month_supports else 0)
    counter_units = len(drain_facts) + (2 if not month_supports else 0)
    total = max(1, support_units + counter_units)
    balance_bp = ((support_units - counter_units) * 10000) // total
    if balance_bp >= 7000:
        strength = "extremely_strong"
    elif balance_bp >= 2500:
        strength = "strong"
    elif balance_bp <= -7000:
        strength = "extremely_weak"
    elif balance_bp <= -2500:
        strength = "weak"
    else:
        strength = "balanced"

    pattern_map = {
        "正官": "proper_officer", "七杀": "seven_killings", "正印": "proper_seal",
        "偏印": "indirect_seal", "正财": "proper_wealth", "偏财": "indirect_wealth",
        "食神": "food_god", "伤官": "hurting_officer", "比肩": "jianlu",
        "劫财": "yang_blade_candidate",
    }
    pattern = pattern_map.get(month_primary, "no_clear_pattern")
    pattern_state = "candidate"
    if strength == "extremely_strong":
        pattern, pattern_state = "follow_strong_candidate", "contested"
    elif strength == "extremely_weak":
        dominant = Counter(visible + hidden).most_common(1)[0][0]
        pattern, pattern_state = f"follow_weak_{pattern_map.get(dominant, 'mixed')}_candidate", "contested"

    day_element = STEM_ELEMENT[day_master]
    producer = next(key for key, value in GENERATES.items() if value == day_element)
    if strength in {"weak", "extremely_weak"}:
        useful = [producer, day_element]
        unfavorable = [GENERATES[day_element], CONTROLS[day_element]]
    elif strength in {"strong", "extremely_strong"}:
        useful = [GENERATES[day_element], CONTROLS[day_element]]
        unfavorable = [producer, day_element]
    else:
        useful = [GENERATES[day_element], producer]
        unfavorable = []
    month_branch = month["branch"]
    climate = "cold" if month_branch in "亥子丑" else "hot" if month_branch in "巳午未" else "temperate"
    climate_candidate = "fire" if climate == "cold" else "water" if climate == "hot" else None
    climate_conflict = bool(climate_candidate and climate_candidate not in useful)

    cycles = []
    for cycle in (fortune_cycles or {}).get("cycles", []):
        stem = cycle["ganzhi"][0] if cycle.get("ganzhi") else None
        element = STEM_ELEMENT.get(stem) if stem else None
        direction = "support" if element in useful else "counter" if element in unfavorable else "neutral"
        annual = []
        for year in cycle.get("annual", []):
            year_element = STEM_ELEMENT[year["ganzhi"][0]] if year.get("ganzhi") else None
            monthly = []
            for month_item in year.get("monthly", []):
                month_element = STEM_ELEMENT[month_item["ganzhi"][0]] if month_item.get("ganzhi") else None
                monthly.append({**month_item, "structural_direction":
                    "support" if month_element in useful else "counter" if month_element in unfavorable else "neutral"})
            annual.append({**year, "monthly": monthly,
                           "structural_direction": "support" if year_element in useful else "counter" if year_element in unfavorable else "neutral"})
        cycles.append({**cycle, "structural_direction": direction, "annual": annual})

    confidence = 9000 if "time" in structure else 6500
    return {
        "profile_id": "bazi-ziping-complete-v1", "ruleset_version": "bazi-ziping-complete-1.0.0",
        "strength": {"status": strength, "balance_bp": balance_bp,
                     "support_units": support_units, "counter_units": counter_units,
                     "month_command_supports": month_supports, "roots": roots,
                     "supporting_evidence": support_facts, "counter_evidence": drain_facts,
                     "confidence_bp": confidence},
        "pattern": {"candidate": pattern, "state": pattern_state, "basis": "month_primary_hidden_ten_god",
                    "supporting_evidence": [month_primary], "counter_evidence": ["strength_extreme"] if pattern_state == "contested" else []},
        "climate": {"state": climate, "adjustment_candidate": climate_candidate, "conflicts_with_balance_method": climate_conflict},
        "useful_elements": {"candidates": useful, "favorable_candidates": useful,
                            "unfavorable_candidates": unfavorable,
                            "status": "contested" if climate_conflict else "provisional",
                            "confidence_bp": min(confidence, 7000)},
        "fortune_cycles": {**(fortune_cycles or {}), "cycles": cycles},
        "source_policy": "pinned_upstream_profile_with_exposed_integer_evidence_units",
        "review_status": "UNCONFIRMED", "production_activatable": False,
    }


SUPPORT_STAR_TYPES = {"soft", "helper", "lucun", "tianma"}
COUNTER_STAR_TYPES = {"tough"}


def ziwei_complete(output: dict) -> dict:
    palaces = output["palaces"]
    results = []
    for palace in palaces:
        i = palace["index"]
        group = [palaces[i], palaces[(i + 4) % 12], palaces[(i + 8) % 12], palaces[(i + 6) % 12]]
        facts = [star for p in group for star in p.get("star_details", [])]
        support_groups = sorted({star["type"] for star in facts if star.get("type") in SUPPORT_STAR_TYPES})
        counter_groups = sorted({star["type"] for star in facts if star.get("type") in COUNTER_STAR_TYPES})
        transformations = sorted({star["mutagen"] for star in facts if star.get("mutagen")})
        evidence_units = len(support_groups) + len(transformations)
        counter_units = len(counter_groups)
        total = max(1, evidence_units + counter_units)
        strength_bp = ((evidence_units - counter_units) * 10000) // total
        confidence_bp = min(9000, 4500 + 500 * len({p["index"] for p in group}) - 300 * counter_units)
        results.append({
            "palace_index": i, "palace_name": palace["name"], "branch": palace["branch"],
            "sanhe_palaces": [p["index"] for p in group[:3]], "opposite_palace": group[3]["index"],
            "major_stars": palace.get("major_stars", []), "support_groups": support_groups,
            "counter_groups": counter_groups, "transformations": transformations,
            "strength_bp": strength_bp, "confidence_bp": confidence_bp,
            "status": "contested" if support_groups and counter_groups else "provisional",
            "supporting_evidence": [f"star_type:{x}" for x in support_groups] + [f"mutagen:{x}" for x in transformations],
            "counter_evidence": [f"star_type:{x}" for x in counter_groups],
        })
    return {
        "profile_id": "ziwei-sanhe-complete-v1", "ruleset_version": "ziwei-sanhe-complete-1.0.0",
        "life_palace_branch": output.get("life_palace_branch"), "body_palace_branch": output.get("body_palace_branch"),
        "five_element_bureau": output.get("five_element_bureau"), "soul_ruler": output.get("soul_ruler"),
        "body_ruler": output.get("body_ruler"), "palaces": results,
        "periods": output.get("horoscope"), "aggregation_policy": "grouped_sanhe_evidence_not_single_star_sum",
        "review_status": "UNCONFIRMED", "production_activatable": False,
    }


QUESTION_TO_LIUQIN = {
    "self": "兄弟", "career": "官鬼", "wealth": "妻财", "relationship": "官鬼",
    "cooperation": "妻财", "travel": "父母", "study": "官鬼", "lost_property": "妻财",
}

BRANCH_COMBINES = {frozenset(pair) for pair in ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")}
BRANCH_HARMS = {frozenset(pair) for pair in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")}
BRANCH_PUNISHMENTS = {frozenset(pair) for pair in ("子卯", "寅巳", "巳申", "申寅", "丑戌", "戌未", "未丑")}
ADVANCE_PAIRS = {tuple(pair) for pair in ("亥子", "寅卯", "巳午", "申酉", "丑辰", "辰未", "未戌", "戌丑")}


def _branch_relation(left: str, right: str) -> list[str]:
    pair = frozenset((left, right))
    result = []
    if left == right:
        result.append("same")
    if BRANCHES[(BRANCHES.index(left) + 6) % 12] == right:
        result.append("clash")
    if pair in BRANCH_COMBINES:
        result.append("combine")
    if pair in BRANCH_HARMS:
        result.append("harm")
    if pair in BRANCH_PUNISHMENTS:
        result.append("punishment_candidate")
    return result


def liuyao_complete(output: dict, value: dict) -> dict:
    primary = output["primary"]
    changed = output.get("changed")
    month_branch = value.get("month_branch")
    day_branch = value.get("day_branch")
    if month_branch is None and value.get("month_branch_index") is not None:
        month_branch = BRANCHES[int(value["month_branch_index"]) % 12]
    if day_branch is None and value.get("day_branch_index") is not None:
        day_branch = BRANCHES[int(value["day_branch_index"]) % 12]
    xunkong = set(value.get("xunkong_branches", []))
    category = value.get("question_type", "general_trend")
    target = QUESTION_TO_LIUQIN.get(category)
    positions = [line["position"] for line in primary["lines"] if target and line["liuqin"] == target]
    chosen = positions[0] if len(positions) == 1 else None
    yongshen = {"question_type": category, "liuqin": target, "candidates": positions,
                "chosen": chosen, "status": "provisional" if chosen else "contested" if positions else "insufficient"}
    target_elements = sorted({line["wuxing"] for line in primary["lines"] if line["position"] in positions})
    forces = []
    support = counter = 0
    for line in primary["lines"]:
        zhi = line["zhi"]
        flags = {"xunkong": zhi in xunkong,
                 "month_break": bool(month_branch and BRANCHES[(BRANCHES.index(month_branch) + 6) % 12] == zhi),
                 "day_clash": bool(day_branch and BRANCHES[(BRANCHES.index(day_branch) + 6) % 12] == zhi)}
        moving = line["position"] in output["moving_lines"]
        relation = None
        changed_zhi = None
        if moving and changed:
            new = changed["lines"][line["position"] - 1]
            changed_zhi = new["zhi"]
            if new["wuxing"] == line["wuxing"]:
                if (zhi, changed_zhi) in ADVANCE_PAIRS:
                    relation = "advance"
                elif (changed_zhi, zhi) in ADVANCE_PAIRS:
                    relation = "retreat"
                else:
                    relation = "same_element_change"
            elif GENERATES.get(new["wuxing"]) == line["wuxing"]:
                relation = "returns_to_generate"
            elif CONTROLS.get(new["wuxing"]) == line["wuxing"]:
                relation = "returns_to_control"
        if line["position"] in positions:
            positive = int(moving) + int(not any(flags.values())) + int(relation == "returns_to_generate")
            negative = int(flags["xunkong"]) + int(flags["month_break"]) + int(relation == "returns_to_control")
            support += positive; counter += negative
        role = "neutral"
        if target_elements:
            target_element = target_elements[0]
            if line["wuxing"] == target_element:
                role = "yongshen_peer"
            elif GENERATES.get(line["wuxing"]) == target_element:
                role = "source_spirit"
            elif CONTROLS.get(line["wuxing"]) == target_element:
                role = "adverse_spirit"
            elif GENERATES.get(target_element) == line["wuxing"]:
                role = "drain_spirit"
        forces.append({"position": line["position"], "flags": flags, "moving": moving,
                       "change_relation": relation, "changed_branch": changed_zhi, "role": role,
                       "month_relations": _branch_relation(zhi, month_branch) if month_branch else [],
                       "day_relations": _branch_relation(zhi, day_branch) if day_branch else [],
                       "fuyin": bool(changed_zhi and changed_zhi == zhi),
                       "fanyin": bool(changed_zhi and BRANCHES[(BRANCHES.index(zhi) + 6) % 12] == changed_zhi)})
    total = max(1, support + counter)
    strength_bp = ((support - counter) * 10000) // total if target else 0
    if not target:
        verdict = "insufficient"
    elif support and counter:
        verdict = "contested"
    elif strength_bp >= 3500:
        verdict = "auspicious_with_obstruction" if counter else "auspicious"
    elif strength_bp <= -3500:
        verdict = "inauspicious_with_relief" if support else "inauspicious"
    else:
        verdict = "neutral"
    return {
        "profile_id": "liuyao-jingfang-najia-v1", "ruleset_version": "liuyao-jingfang-najia-1.0.0",
        "question": yongshen, "primary": primary, "changed": changed, "moving_lines": output["moving_lines"],
        "line_forces": forces, "strength_bp": strength_bp,
        "structural_flags": {"fuyin_positions": [x["position"] for x in forces if x["fuyin"]],
                             "fanyin_positions": [x["position"] for x in forces if x["fanyin"]]},
        "confidence_bp": 8500 if target and month_branch and day_branch else 4500 if target else 2000,
        "verdict": verdict, "timing": {"precision": "range", "triggers": sorted({x for x in (month_branch, day_branch) if x})},
        "supporting_evidence": [f"support_unit:{i+1}" for i in range(support)],
        "counter_evidence": [f"counter_unit:{i+1}" for i in range(counter)],
        "disputes": [] if target else ["no_unique_yongshen_without_explicit_question_type"],
        "review_status": "UNCONFIRMED", "production_activatable": False,
    }
