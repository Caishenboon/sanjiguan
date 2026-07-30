"""Fail-closed prose-only contract for Sprint 18 life-trend reports."""
from __future__ import annotations

import re
from copy import deepcopy

from sanji_engine.canonical import content_hash

FIELDS = {
    "chapter", "image_text", "plain_interpretation", "past",
    "current", "future", "action_guidance",
}
PSEUDO_CLASSIC = ("经云", "古云", "卦曰", "象曰", "某经载", "古籍记载")
CERTAINTY_ESCALATIONS = ("必然", "注定", "一定会", "毫无疑问", "唯一结局")
AUSPICE_LABELS = {
    "吉", "平", "凶", "吉中有阻", "凶中有解", "吉凶相争",
    "资料不足，暂不定吉凶",
}
DATE_PATTERN = re.compile(
    r"(?<!\d)\d{4}(?:-\d{2}(?:-\d{2})?)?(?!\d)|"
    r"(?<!\d)\d{4}年(?:\d{1,2}月(?:\d{1,2}日)?)?(?!\d)"
)


def deterministic_narrative(core: dict) -> dict:
    report = core["deterministic_report"]
    return {
        "chapter": report["chapter"],
        "image_text": report["image_text"],
        "plain_interpretation": report["plain_interpretation"],
        "past": report["past"],
        "current": report["current"],
        "future": report["future"],
        "action_guidance": report["action_guidance"],
    }


def build_narrative_payload(core: dict) -> dict:
    """Return only the allowlisted, structure-locked provider payload."""
    source = core["narrative_input"]
    value = {
        "prompt_version": "life-trend-report-1.0.0",
        "core_output_hash": core["core_output_hash"],
        "narrative_input_hash": core["narrative_input_hash"],
        "report_outline": deepcopy(source["report_outline"]),
        "locked_timeline": deepcopy(source["locked_timeline"]),
        "locked_timing_windows": deepcopy(source["locked_timing_windows"]),
        "protected_entities": deepcopy(source["protected_entities"]),
        "epistemic_suffixes": deepcopy(source["epistemic_suffixes"]),
    }
    return {**value, "payload_hash": content_hash(value)}


def _normalize_chinese_date(value: str) -> str:
    match = re.fullmatch(
        r"(\d{4})年(?:(\d{1,2})月(?:(\d{1,2})日)?)?", value
    )
    if not match:
        return value
    year, month, day = match.groups()
    if day:
        return f"{year}-{int(month):02d}-{int(day):02d}"
    if month:
        return f"{year}-{int(month):02d}"
    return year


def validate_life_trend_narrative(prose: dict, core: dict) -> dict:
    """Reject prose that changes a locked fact or weakens epistemic status."""
    if not isinstance(prose, dict) or set(prose) != FIELDS:
        raise ValueError("invalid_life_trend_narrative_schema")
    if any(
        not isinstance(prose[field], str) or not prose[field].strip()
        for field in FIELDS
    ):
        raise ValueError("empty_life_trend_narrative_field")
    text = "\n".join(prose[field] for field in sorted(FIELDS))
    if any(token in text for token in PSEUDO_CLASSIC):
        raise ValueError("pseudo_classic_rejected")
    if any(token in text for token in CERTAINTY_ESCALATIONS):
        raise ValueError("certainty_escalation_rejected")
    narrative_input = core["narrative_input"]
    allowed_dates = {
        str(value)
        for window in narrative_input["locked_timing_windows"]
        for value in (window["start"], window["end"])
    }
    allowed_dates |= {item[:7] for item in allowed_dates} | {
        item[:4] for item in allowed_dates
    }
    for found in DATE_PATTERN.findall(text):
        if _normalize_chinese_date(found) not in allowed_dates:
            raise ValueError("unauthorized_precise_date_rejected")
    for display in narrative_input.get("protected_entities", []):
        base = display.split("【", 1)[0]
        if base in text and display not in text:
            raise ValueError("epistemic_suffix_removed")
    locked_auspice = core["deterministic_report"]["auspice"]
    mentioned = {label for label in AUSPICE_LABELS if label in text}
    if mentioned and locked_auspice not in mentioned:
        raise ValueError("auspice_override_rejected")
    return deepcopy(prose)


def controlled_narrative_or_fallback(
    core: dict, provider_output: dict | None, provider_error: Exception | None = None
) -> dict:
    """Always return a complete deterministic report on provider failure."""
    fallback = deterministic_narrative(core)
    if provider_error is not None or provider_output is None:
        return {
            "source": "deterministic_template",
            "status": "fallback",
            "fallback_reason": (
                type(provider_error).__name__ if provider_error
                else "provider_unavailable"
            ),
            "content": fallback,
            "narrative_output_hash": content_hash(fallback),
        }
    try:
        accepted = validate_life_trend_narrative(provider_output, core)
    except (TypeError, ValueError) as exc:
        return {
            "source": "deterministic_template",
            "status": "rejected_fallback",
            "fallback_reason": str(exc),
            "content": fallback,
            "narrative_output_hash": content_hash(fallback),
        }
    return {
        "source": "deepseek",
        "status": "accepted",
        "fallback_reason": None,
        "content": accepted,
        "narrative_output_hash": content_hash(accepted),
    }
