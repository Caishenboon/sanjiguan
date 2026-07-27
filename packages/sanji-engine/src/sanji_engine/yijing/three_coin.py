from __future__ import annotations

from copy import deepcopy

from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID
from .assets import load_hexagrams

METHOD_ID = "YIJING.THREE_COIN.PHYSICAL.MECHANICAL.V1"
METHOD_VERSION = "1.0.0"
INPUT_ORDER = "bottom_to_top"

LINE_STATES = {
    6: ("old_yin", 0, True, 1),
    7: ("young_yang", 1, False, 1),
    8: ("young_yin", 0, False, 0),
    9: ("old_yang", 1, True, 0),
}
TRIGRAMS = {
    "111": {"name": "乾", "key": "111"},
    "110": {"name": "兑", "key": "110"},
    "101": {"name": "离", "key": "101"},
    "100": {"name": "震", "key": "100"},
    "011": {"name": "巽", "key": "011"},
    "010": {"name": "坎", "key": "010"},
    "001": {"name": "艮", "key": "001"},
    "000": {"name": "坤", "key": "000"},
}


def _validate_tosses(snapshot: dict) -> list[dict]:
    allowed = {"operation", "method_id", "method_version", "input_order", "tosses"}
    unexpected = sorted(set(snapshot) - allowed)
    if unexpected:
        raise EngineError(INPUT_INVALID, "unsupported three-coin input fields", {"fields": unexpected})
    if snapshot.get("operation") != "cast_physical_three_coin":
        raise EngineError(INPUT_INVALID, "yijing operation is not supported")
    if snapshot.get("method_id") != METHOD_ID or snapshot.get("method_version") != METHOD_VERSION:
        raise EngineError(INPUT_INVALID, "three-coin method version is not supported")
    if snapshot.get("input_order") != INPUT_ORDER:
        raise EngineError(INPUT_INVALID, "six tosses must be explicitly ordered bottom_to_top")
    tosses = snapshot.get("tosses")
    if not isinstance(tosses, list) or len(tosses) != 6:
        raise EngineError(INPUT_INVALID, "exactly six tosses are required")
    normalized = []
    for expected_position, toss in enumerate(tosses, 1):
        if not isinstance(toss, dict) or set(toss) != {"line_position", "coin_values"}:
            raise EngineError(INPUT_INVALID, "each toss requires only line_position and coin_values")
        if type(toss["line_position"]) is not int or toss["line_position"] != expected_position:
            raise EngineError(INPUT_INVALID, "line positions must be 1 through 6, bottom to top")
        coins = toss["coin_values"]
        if (
            not isinstance(coins, list)
            or len(coins) != 3
            or any(type(value) is not int or value not in {2, 3} for value in coins)
        ):
            raise EngineError(INPUT_INVALID, "each toss requires exactly three integer coin values of 2 or 3")
        normalized.append({"line_position": expected_position, "coin_values": deepcopy(coins)})
    return normalized


def cast_physical_three_coin(snapshot: dict) -> tuple[dict, list[dict], dict]:
    tosses = _validate_tosses(snapshot)
    mapping, asset = load_hexagrams()
    lines = []
    trace = []
    for toss in tosses:
        value = sum(toss["coin_values"])
        state, base, moving, transformed = LINE_STATES[value]
        position = toss["line_position"]
        trigram_contribution = "lower" if position <= 3 else "upper"
        line = {
            **toss,
            "sum": value,
            "line_state": state,
            "base_polarity": base,
            "moving": moving,
            "transformed_polarity": transformed,
            "trigram_contribution": trigram_contribution,
        }
        lines.append(line)
        step = {
            "step_id": f"yijing:{position:03d}:derive_line",
            "sequence": position * 10,
            "module_id": "yijing",
            "operation": "derive_three_coin_line",
            "input_refs": [f"input:tosses[{position - 1}]"],
            "rule_refs": [METHOD_ID],
            "source_refs": asset["source_ids"],
            "parameters": line,
            "output_refs": [f"yijing:line:{position}"],
        }
        trace.append({**step, "calculation_hash": content_hash(step)})
    base_key = "".join(str(line["base_polarity"]) for line in lines)
    transformed_key = "".join(str(line["transformed_polarity"]) for line in lines)
    lower = TRIGRAMS[base_key[:3]]
    upper = TRIGRAMS[base_key[3:]]
    transformed_lower = TRIGRAMS[transformed_key[:3]]
    transformed_upper = TRIGRAMS[transformed_key[3:]]
    base_hexagram = mapping[base_key]
    transformed_hexagram = mapping[transformed_key]
    moving_lines = [line["line_position"] for line in lines if line["moving"]]
    result = {
        "module": "yijing",
        "method_id": METHOD_ID,
        "method_version": METHOD_VERSION,
        "method_class": "traditional_mechanical",
        "ruleset_id": "yijing-three-coin-mechanical-0.1.0",
        "ruleset_status": "research_active",
        "production_activatable": False,
        "input_order": INPUT_ORDER,
        "tosses": tosses,
        "lines": lines,
        "moving_lines": moving_lines,
        "lower_trigram": lower,
        "upper_trigram": upper,
        "base_hexagram": {
            "key": base_key,
            "sequence": base_hexagram["sequence"],
            "name": base_hexagram["name"],
        },
        "transformed_lower_trigram": transformed_lower,
        "transformed_upper_trigram": transformed_upper,
        "transformed_hexagram": {
            "key": transformed_key,
            "sequence": transformed_hexagram["sequence"],
            "name": transformed_hexagram["name"],
        },
        "has_transformed_hexagram": bool(moving_lines),
        "mapping_asset": asset,
        "interpretation": None,
        "auspiciousness": None,
        "manifestation_period": None,
    }
    lookup = {
        "step_id": "yijing:070:assemble_and_lookup_hexagrams",
        "sequence": 70,
        "module_id": "yijing",
        "operation": "assemble_trigrams_and_lookup_king_wen_sequence",
        "input_refs": [f"yijing:line:{position}" for position in range(1, 7)],
        "rule_refs": [METHOD_ID],
        "source_refs": asset["source_ids"],
        "parameters": {
            "base_hexagram_key": base_key,
            "transformed_hexagram_key": transformed_key,
            "moving_lines": moving_lines,
            "mapping_asset_version": asset["asset_version"],
            "ruleset_version": "0.1.0",
        },
        "output_refs": ["yijing:base_hexagram", "yijing:transformed_hexagram"],
    }
    trace.append({**lookup, "calculation_hash": content_hash(lookup)})
    return result, trace, {
        "yijing_domain_hash": content_hash(result),
        "mapping_asset_hash": asset["content_hash"],
    }
