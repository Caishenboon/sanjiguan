from __future__ import annotations

from decimal import Decimal, InvalidOperation

from ..errors import EngineError, INPUT_INVALID

ALLOWED_DIRECTIONS = {"support", "oppose"}
ALLOWED_DOMAINS = {
    "ming", "karma", "vow", "dream", "relation", "life_event", "sensation", "gua"
}
REQUIRED_FIELDS = {
    "id", "domain", "tag", "direction", "strength", "source_reliability",
    "relevance", "independence_group",
}


def _ratio(value: object, path: str) -> float:
    # Public Engine validation rejects binary floats. Internal floats are
    # accepted only after the compatibility decoder restores frozen inputs.
    if not isinstance(value, (str, int, float)):
        raise EngineError(INPUT_INVALID, f"{path} must be a decimal string")
    try:
        decimal = Decimal(str(value))
    except InvalidOperation as exc:
        raise EngineError(INPUT_INVALID, f"{path} is not numeric") from exc
    if decimal < 0 or decimal > 1:
        raise EngineError(INPUT_INVALID, f"{path} must be within [0, 1]")
    return float(decimal)


def validate_signals(signals: object) -> list[dict]:
    if not isinstance(signals, list):
        raise EngineError(INPUT_INVALID, "signals must be an array")
    seen_ids: set[str] = set()
    validated: list[dict] = []
    for index, source in enumerate(signals):
        if not isinstance(source, dict):
            raise EngineError(INPUT_INVALID, f"signals[{index}] must be an object")
        missing = sorted(REQUIRED_FIELDS - source.keys())
        if missing:
            raise EngineError(
                INPUT_INVALID, f"signals[{index}] is incomplete", {"fields": missing}
            )
        signal_id = source["id"]
        if not isinstance(signal_id, str) or not signal_id.strip():
            raise EngineError(INPUT_INVALID, f"signals[{index}].id is invalid")
        if signal_id in seen_ids:
            raise EngineError(INPUT_INVALID, "duplicate signal id", {"signal_id": signal_id})
        seen_ids.add(signal_id)
        if source["domain"] not in ALLOWED_DOMAINS:
            raise EngineError(INPUT_INVALID, "unknown signal domain", {"signal_id": signal_id})
        if not isinstance(source["tag"], str) or not source["tag"].strip():
            raise EngineError(INPUT_INVALID, "unknown or empty signal type", {"signal_id": signal_id})
        if source["direction"] not in ALLOWED_DIRECTIONS:
            raise EngineError(INPUT_INVALID, "invalid signal direction", {"signal_id": signal_id})
        group = source["independence_group"]
        if not isinstance(group, str) or not group.strip():
            raise EngineError(
                INPUT_INVALID, "signal source/independence group is missing",
                {"signal_id": signal_id},
            )
        item = dict(source)
        item["strength"] = _ratio(source["strength"], f"signals[{index}].strength")
        item["source_reliability"] = _ratio(
            source["source_reliability"], f"signals[{index}].source_reliability"
        )
        item["relevance"] = _ratio(source["relevance"], f"signals[{index}].relevance")
        item["ordinary_explanation_present"] = bool(
            source.get("ordinary_explanation_present", False)
        )
        validated.append(item)
    return validated


def deduplicate_signals(signals: list[dict]) -> tuple[list[dict], list[dict]]:
    """Preserve the legacy first-seen group order and equal-value tie behavior."""
    strongest: dict[str, tuple[float, dict]] = {}
    decisions: list[dict] = []
    for input_index, signal in enumerate(signals):
        group = signal["independence_group"]
        magnitude = (
            signal["strength"] * signal["source_reliability"] * signal["relevance"]
        )
        previous = strongest.get(group)
        retained = previous is None or magnitude > previous[0]
        if retained:
            strongest[group] = (magnitude, signal)
        decisions.append(
            {
                "signal_id": signal["id"],
                "input_index": input_index,
                "independence_group": group,
                "magnitude": round(magnitude, 8),
                "retained_at_step": retained,
                "tie_policy": "first_seen_wins",
            }
        )
    retained_ids = {item[1]["id"] for item in strongest.values()}
    for decision in decisions:
        decision["retained_final"] = decision["signal_id"] in retained_ids
    return [item[1] for item in strongest.values()], decisions
