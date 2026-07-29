"""Canonical mechanical-fact adapters.

Adapters expose only facts already calculated by the isolated deterministic
modules.  They do not interpret facts or create Signal v2 values.
"""
from __future__ import annotations

from copy import deepcopy

from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID

SUPPORTED_SYSTEMS = {"yijing", "bazi", "ziwei"}


def adapt_mechanical_facts(source_system: str, result: dict, profile_id: str | None) -> list[dict]:
    if source_system not in SUPPORTED_SYSTEMS or not isinstance(result, dict):
        raise EngineError(INPUT_INVALID, "mechanical fact adapter input is invalid")
    selectors = {
        "yijing": (
            "lines", "primary_hexagram", "changed_hexagram", "moving_line_positions",
            "yin_yang_structure",
        ),
        "bazi": (
            "pillars", "five_element_counts", "yin_yang_counts", "hidden_stems",
            "day_master", "ten_god_relations", "month_command", "structural_relations",
            "candidates", "boundary_flags",
        ),
        "ziwei": (
            "life_palace", "body_palace", "palaces", "major_stars",
            "approved_supporting_stars", "transformations", "trines", "cycles",
        ),
    }[source_system]
    facts: list[dict] = []
    for field in selectors:
        if field not in result:
            continue
        base = {
            "fact_id": f"{source_system}:{field}",
            "source_system": source_system,
            "source_fact_path": f"$.{field}",
            "profile_id": profile_id,
            "value": deepcopy(result[field]),
        }
        facts.append({**base, "content_hash": content_hash(base)})
    return sorted(facts, key=lambda value: value["fact_id"])
