"""Deterministic life-trend timeline, OHLC and Sanji report structure v1.

This is a Sanji-original, unconfirmed research model. It is not a traditional
K-line method and it does not establish real-world predictive accuracy.
"""
from __future__ import annotations

import json
from calendar import monthrange
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from importlib.resources import files

from .. import __version__
from ..canonical import content_hash
from ..errors import EngineError, INPUT_INVALID

OPERATION = "run_life_trend_v1"
METHOD_ID = "LIFE_TREND.SANJI_ORIGINAL.RESEARCH.V1"
RULESET_VERSION = "life-trend-rules/1.0.0"
REPORT_TEMPLATE_VERSION = "sanji-report-template/1.0.0"
EVIDENCE_POLICY_VERSION = "liuxiang-user-evidence-policy/1.0.0"

ALLOWED_PRECISIONS = {"exact_date", "month_only", "quarter", "year_only", "phase", "unknown"}
ALLOWED_DIRECTIONS = {"supports", "counters", "neutral"}
ALLOWED_KINDS = {
    "coverage", "structural", "evidence", "event", "projection",
}
ALLOWED_EPISTEMIC = {
    "observed", "mechanically_derived", "rule_inferred", "generated_identity",
    "historical_candidate", "contested", "insufficient",
}
FORBIDDEN_TEXT_FIELDS = {
    "raw_narrative", "dream_text", "journal_text", "relationship_text",
    "prompt", "llm_output", "oracle_output", "provider_debug",
}
SEGMENT_ORDER = {
    "observed_past": 0,
    "current_state": 1,
    "projected_future": 2,
    "insufficient_gap": 3,
}


def _load(name: str) -> dict:
    return json.loads(
        files("sanji_engine").joinpath(f"rulesets/assets/{name}").read_text(encoding="utf-8")
    )


def load_life_trend_rules() -> dict:
    asset = _load("life-trend-rules-1.0.0.json")
    expected = asset["content_hash"]
    actual = content_hash({key: value for key, value in asset.items() if key != "content_hash"})
    if expected != actual:
        raise EngineError(INPUT_INVALID, "life trend ruleset content hash mismatch")
    return asset


def _clamp(value: int, low: int = -10_000, high: int = 10_000) -> int:
    return max(low, min(high, int(value)))


def _parse_as_of(value: str) -> date:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(
            timezone.utc
        ).date()
    except ValueError as exc:
        raise EngineError(INPUT_INVALID, "life trend as_of is invalid") from exc


def _date_interval(value: str | None, precision: str) -> tuple[date, date] | None:
    if not value or precision == "unknown":
        return None
    try:
        if precision == "exact_date":
            item = date.fromisoformat(value)
            return item, item
        if precision == "month_only":
            year, month = (int(part) for part in value.split("-"))
            return date(year, month, 1), date(year, month, monthrange(year, month)[1])
        if precision == "quarter":
            year_text, quarter_text = value.split("-Q")
            year, quarter = int(year_text), int(quarter_text)
            month = (quarter - 1) * 3 + 1
            end_month = month + 2
            return date(year, month, 1), date(
                year, end_month, monthrange(year, end_month)[1]
            )
        if precision == "year_only":
            year = int(value)
            return date(year, 1, 1), date(year, 12, 31)
        if precision == "phase":
            start, end = (int(part) for part in value.split("-", 1))
            return date(start, 1, 1), date(end, 12, 31)
    except (TypeError, ValueError) as exc:
        raise EngineError(INPUT_INVALID, "factor date does not match precision") from exc
    raise EngineError(INPUT_INVALID, "factor date precision is unsupported")


def _normalize_factor(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise EngineError(INPUT_INVALID, "life trend factor must be an object")
    forbidden = sorted(FORBIDDEN_TEXT_FIELDS & set(raw))
    if forbidden:
        raise EngineError(
            INPUT_INVALID,
            "private narrative or provider data is forbidden in life trend input",
            {"fields": forbidden},
        )
    factor_id = raw.get("factor_id")
    if not isinstance(factor_id, str) or not factor_id:
        raise EngineError(INPUT_INVALID, "life trend factor requires factor_id")
    precision = raw.get("date_precision", "unknown")
    if precision not in ALLOWED_PRECISIONS:
        raise EngineError(INPUT_INVALID, "life trend factor precision is invalid")
    direction = raw.get("direction", "neutral")
    if direction not in ALLOWED_DIRECTIONS:
        raise EngineError(INPUT_INVALID, "life trend factor direction is invalid")
    kind = raw.get("factor_kind", "evidence")
    if kind not in ALLOWED_KINDS:
        raise EngineError(INPUT_INVALID, "life trend factor kind is invalid")
    epistemic = raw.get("epistemic_status", "observed")
    if epistemic not in ALLOWED_EPISTEMIC:
        raise EngineError(INPUT_INVALID, "life trend epistemic status is invalid")
    magnitude = int(raw.get("magnitude_bp", 0))
    reliability = int(raw.get("source_reliability_bp", 6000))
    mapping_reliability = int(raw.get("mapping_reliability_bp", 6000))
    if not 0 <= magnitude <= 10_000:
        raise EngineError(INPUT_INVALID, "life trend magnitude is invalid")
    if not 0 <= reliability <= 10_000 or not 0 <= mapping_reliability <= 10_000:
        raise EngineError(INPUT_INVALID, "life trend reliability is invalid")
    rule_id = str(raw.get("rule_id") or "LIFE_TREND.FACT.NORMALIZE.V1")
    source_system = str(raw.get("source_system") or "user_record")
    protected_entities = []
    for item in raw.get("protected_entities", []):
        if not isinstance(item, dict) or not isinstance(item.get("value"), str):
            raise EngineError(INPUT_INVALID, "protected entity must contain a string value")
        protected_entities.append({
            "value": item["value"],
            "epistemic_status": str(item.get("epistemic_status") or "rule_inferred"),
            "display_value": str(item.get("display_value") or item["value"]),
        })
    # Topic and mechanical outputs remain structural references. They cannot
    # recursively become life evidence or move the K-line without an explicit
    # versioned life-trend projection rule.
    scoring_allowed = epistemic == "observed" and kind in {"evidence", "event"}
    if kind == "projection":
        scoring_allowed = (
            epistemic == "rule_inferred"
            and source_system == "life_trend"
            and rule_id.startswith("LIFE_TREND.")
        )
    if kind in {"coverage", "structural"} or not scoring_allowed:
        magnitude = 0
        direction = "neutral"
    interval = _date_interval(raw.get("occurred_on"), precision)
    value = {
        "factor_id": factor_id,
        "factor_type": str(raw.get("factor_type") or "unspecified"),
        "factor_kind": kind,
        "source_system": source_system,
        "source_record_id": str(raw.get("source_record_id") or factor_id),
        "source_execution_id": raw.get("source_execution_id"),
        "occurred_on": raw.get("occurred_on"),
        "date_precision": precision,
        "interval_start": interval[0].isoformat() if interval else None,
        "interval_end": interval[1].isoformat() if interval else None,
        "direction": direction,
        "magnitude_bp": magnitude,
        "source_reliability_bp": reliability,
        "mapping_reliability_bp": mapping_reliability,
        "independence_group": str(raw.get("independence_group") or factor_id),
        "shared_source_group": str(raw.get("shared_source_group") or factor_id),
        "epistemic_status": epistemic,
        "boundary_sensitive": bool(raw.get("boundary_sensitive", False)),
        "conflict": bool(raw.get("conflict", False)),
        "tags": sorted(set(str(tag) for tag in raw.get("tags", []))),
        "rule_id": rule_id,
        "rule_version": str(raw.get("rule_version") or "1.0.0"),
        "source_refs": sorted(set(str(ref) for ref in raw.get("source_refs", []))),
        "protected_entities": sorted(
            protected_entities,
            key=lambda item: (item["value"], item["epistemic_status"]),
        ),
        "scoring_allowed": scoring_allowed,
    }
    return {**value, "content_hash": content_hash(value)}


def _precision_rank(precision: str) -> int:
    return {
        "exact_date": 0, "month_only": 1, "quarter": 2,
        "year_only": 3, "phase": 4, "unknown": 5,
    }[precision]


def _choose_granularity(
    requested: str, factors: list[dict], start: date, end: date
) -> str:
    allowed = {"auto", "day", "month", "quarter", "year", "phase"}
    if requested not in allowed:
        raise EngineError(INPUT_INVALID, "life trend granularity is invalid")
    if requested != "auto":
        return requested
    known = [factor["date_precision"] for factor in factors if factor["interval_start"]]
    coarsest = max(known, key=_precision_rank, default="unknown")
    span_days = max(0, (end - start).days)
    if coarsest in {"phase", "unknown"} or span_days > 3650:
        return "phase"
    if coarsest == "year_only" or span_days > 730:
        return "year"
    if coarsest == "quarter" or span_days > 365:
        return "quarter"
    if coarsest == "month_only" or span_days > 90:
        return "month"
    return "day"


def _bucket_key(value: date, granularity: str) -> str:
    if granularity == "day":
        return value.isoformat()
    if granularity == "month":
        return f"{value.year:04d}-{value.month:02d}"
    if granularity == "quarter":
        return f"{value.year:04d}-Q{((value.month - 1) // 3) + 1}"
    if granularity == "year":
        return str(value.year)
    phase_start = value.year - (value.year % 5)
    return f"{phase_start:04d}-{phase_start + 4:04d}"


def _bucket_interval(key: str, granularity: str) -> tuple[date, date, str]:
    if granularity == "day":
        value = date.fromisoformat(key)
        return value, value, "exact_date"
    if granularity == "month":
        year, month = (int(part) for part in key.split("-"))
        return date(year, month, 1), date(year, month, monthrange(year, month)[1]), "month_only"
    if granularity == "quarter":
        year_text, quarter_text = key.split("-Q")
        year, quarter = int(year_text), int(quarter_text)
        month = (quarter - 1) * 3 + 1
        end_month = month + 2
        return date(year, month, 1), date(
            year, end_month, monthrange(year, end_month)[1]
        ), "quarter"
    if granularity == "year":
        year = int(key)
        return date(year, 1, 1), date(year, 12, 31), "year_only"
    start, end = (int(part) for part in key.split("-", 1))
    return date(start, 1, 1), date(end, 12, 31), "phase"


def _date_value(value: date, granularity: str) -> tuple[str, str]:
    key = _bucket_key(value, granularity)
    return key, {
        "day": "exact_date",
        "month": "month_only",
        "quarter": "quarter",
        "year": "year_only",
        "phase": "phase",
    }[granularity]


def _advance(value: date, granularity: str) -> date:
    if granularity == "day":
        return value + timedelta(days=1)
    if granularity == "month":
        return date(value.year + (value.month == 12), 1 if value.month == 12 else value.month + 1, 1)
    if granularity == "quarter":
        month = value.month + 3
        return date(value.year + ((month - 1) // 12), ((month - 1) % 12) + 1, 1)
    if granularity == "year":
        return date(value.year + 1, 1, 1)
    return date(value.year + 5, 1, 1)


def _supports_precision(factor_precision: str, granularity: str) -> bool:
    required = {
        "day": 0, "month": 1, "quarter": 2, "year": 3, "phase": 4,
    }[granularity]
    return _precision_rank(factor_precision) <= required


def _deduplicate(factors: list[dict]) -> tuple[list[dict], list[dict]]:
    groups: dict[str, list[dict]] = {}
    for factor in factors:
        groups.setdefault(factor["shared_source_group"], []).append(factor)
    retained, decisions = [], []
    for group in sorted(groups):
        members = sorted(
            groups[group],
            key=lambda item: (
                -(item["magnitude_bp"] * item["source_reliability_bp"]),
                item["factor_id"],
                item["content_hash"],
            ),
        )
        retained.append(members[0])
        decisions.append({
            "shared_source_group": group,
            "retained_factor_id": members[0]["factor_id"],
            "discounted_factor_ids": sorted(item["factor_id"] for item in members[1:]),
            "policy": "single_strongest_factor_per_shared_source_group",
        })
    return sorted(retained, key=lambda item: item["content_hash"]), decisions


def _factor_delta(factor: dict, return_bp: int, cap: int) -> int:
    if not factor["scoring_allowed"]:
        return 0
    amount = (
        factor["magnitude_bp"]
        * factor["source_reliability_bp"]
        * factor["mapping_reliability_bp"]
        * return_bp
        // 1_000_000_000_000
    )
    amount = min(cap, amount)
    return amount if factor["direction"] == "supports" else -amount


def _segment(start: date, end: date, as_of: date, has_data: bool) -> str:
    if not has_data:
        return "insufficient_gap"
    if end < as_of:
        return "observed_past"
    if start <= as_of <= end:
        return "current_state"
    return "projected_future"


def _confidence(
    factors: list[dict], segment: str, distance: int, rules: dict
) -> tuple[int, int]:
    if not factors:
        return 0, 0
    channels = {factor["factor_type"] for factor in factors}
    coverage = min(10_000, len(channels) * rules["coverage_per_channel_bp"])
    effective = [factor for factor in factors if factor["scoring_allowed"]]
    if not effective:
        base = coverage // 2
    else:
        reliability = sum(
            factor["source_reliability_bp"] * factor["mapping_reliability_bp"] // 10_000
            for factor in effective
        ) // len(effective)
        independent = len({factor["independence_group"] for factor in effective})
        base = min(
            10_000,
            coverage * 35 // 100
            + reliability * 45 // 100
            + min(2000, independent * 650),
        )
    base -= sum(rules["boundary_penalty_bp"] for factor in factors if factor["boundary_sensitive"])
    base -= sum(rules["conflict_penalty_bp"] for factor in factors if factor["conflict"])
    if segment == "projected_future":
        schedule = rules["future_confidence_decay_bp"]
        base = base * schedule[min(distance, len(schedule) - 1)] // 10_000
    return _clamp(base, 0, 10_000), coverage


def _auspice(bucket: dict, rules: dict) -> dict:
    candle = bucket["candle"]
    if candle is None or bucket["confidence_bp"] < rules["auspice"]["minimum_confidence_bp"]:
        state = "insufficient"
        rule = "LIFE_TREND.AUSPICE.INSUFFICIENT.V1"
    elif bucket["conflict_count"] > 0 or (
        bucket["support_count"] and bucket["counter_count"]
        and abs(candle["close"]) < rules["auspice"]["direction_threshold_bp"]
    ):
        state, rule = "contested", "LIFE_TREND.AUSPICE.CONTESTED.V1"
    elif candle["close"] >= rules["auspice"]["direction_threshold_bp"]:
        state = "auspicious_with_obstruction" if bucket["counter_count"] else "auspicious"
        rule = "LIFE_TREND.AUSPICE.POSITIVE.V1"
    elif candle["close"] <= -rules["auspice"]["direction_threshold_bp"]:
        state = "inauspicious_with_relief" if bucket["support_count"] else "inauspicious"
        rule = "LIFE_TREND.AUSPICE.NEGATIVE.V1"
    else:
        state, rule = "neutral", "LIFE_TREND.AUSPICE.NEUTRAL.V1"
    return {
        "state": state,
        "label": rules["auspice_labels"][state],
        "rule_id": rule,
        "supporting_factor_ids": bucket["supporting_factor_ids"],
        "counterevidence_factor_ids": bucket["counterevidence_factor_ids"],
        "confidence_bp": bucket["confidence_bp"],
        "trace_ref": f"trace:auspice:{bucket['bucket_id']}",
    }


def _timing_window(bucket: dict) -> dict:
    tags = set(bucket["tags"])
    if bucket["status"] == "insufficient":
        kind = "insufficient"
    elif "relationship" in tags:
        kind = "relationship_window"
    elif "transition" in tags:
        kind = "transition_window"
    elif "completion" in tags:
        kind = "completion_window"
    elif bucket["candle"] and bucket["candle"]["close"] < -800:
        kind = "obstruction_window"
    elif bucket["candle"] and bucket["candle"]["close"] > 800:
        kind = "action_window"
    else:
        kind = "change_window"
    return {
        "window_id": f"timing:{bucket['bucket_id']}",
        "start": bucket["start"],
        "end": bucket["end"],
        "time_precision": bucket["time_precision"],
        "type": kind,
        "trigger_conditions": bucket["driver_factor_ids"],
        "enhancing_factor_ids": bucket["supporting_factor_ids"],
        "weakening_factor_ids": bucket["counterevidence_factor_ids"],
        "strength_bp": abs(bucket["candle"]["close"]) if bucket["candle"] else 0,
        "confidence_bp": bucket["confidence_bp"],
        "status": bucket["status"],
        "supporting_factor_ids": bucket["supporting_factor_ids"],
        "counterevidence_factor_ids": bucket["counterevidence_factor_ids"],
        "trace_ref": f"trace:timing:{bucket['bucket_id']}",
    }


def _bucket_status(bucket: dict, rules: dict) -> str:
    if bucket["candle"] is None or bucket["confidence_bp"] < rules["status"]["minimum_confidence_bp"]:
        return "insufficient"
    if bucket["conflict_count"] or (
        bucket["support_count"] and bucket["counter_count"]
        and abs(bucket["candle"]["close"] - bucket["candle"]["open"])
        <= rules["status"]["contested_delta_bp"]
    ):
        return "contested"
    if (
        bucket["confidence_bp"] >= rules["status"]["decisive_confidence_bp"]
        and abs(bucket["candle"]["close"] - bucket["candle"]["open"])
        >= rules["status"]["decisive_delta_bp"]
    ):
        return "decisive"
    return "provisional"


def _report_text(result: dict, rules: dict) -> dict:
    buckets = result["buckets"]
    past = [bucket for bucket in buckets if bucket["segment"] == "observed_past"]
    current = [bucket for bucket in buckets if bucket["segment"] == "current_state"]
    future = [bucket for bucket in buckets if bucket["segment"] == "projected_future"]
    effective = [bucket for bucket in buckets if bucket["candle"] is not None]
    latest = effective[-1] if effective else None
    state = latest["auspice"]["state"] if latest else "insufficient"
    labels = rules["auspice_labels"]
    title = rules["symbolic_titles"].get(state, rules["symbolic_titles"]["insufficient"])
    if latest:
        movement = latest["candle"]["close"] - latest["candle"]["open"]
        movement_text = "势位上行" if movement > 0 else "势位回落" if movement < 0 else "势位持平"
    else:
        movement_text = "资料尚未形成有效势位"
    missing = sorted({
        item for bucket in buckets for item in bucket["missing"]
    })
    support = sorted({
        item for bucket in buckets for item in bucket["supporting_factor_ids"]
    })
    counters = sorted({
        item for bucket in buckets for item in bucket["counterevidence_factor_ids"]
    })
    contested = sorted({
        bucket["bucket_id"] for bucket in buckets if bucket["status"] == "contested"
    })
    action = {
        "auspicious": "可在已核实条件内稳步推进。",
        "auspicious_with_obstruction": "可进，但应先处理已列逆证与阻滞。",
        "inauspicious": "宜止损守界，暂缓扩大承诺。",
        "inauspicious_with_relief": "先守后动，保留已出现的缓解条件。",
        "contested": "诸势相争，先补充关键证据再决定进退。",
        "neutral": "守常观察，以新增事实校正后续窗口。",
        "insufficient": "资料不足，先补记录，不强造吉凶与应期。",
    }[state]
    structure = {
        "chapter": f"{title} · {labels[state]}",
        "symbolic_title": title,
        "image_text": f"长卷依时展开，{movement_text}；明处据实落笔，空处仍留白。",
        "plain_interpretation": (
            f"本报告按{result['granularity']}时间桶汇总去重后的授权事实。"
            f"当前吉凶状态为“{labels[state]}”，未来窗口均为规则推演，"
            "不会把结构引用或资料数量直接当作势位。"
        ),
        "past": (
            f"往际共有{len(past)}个时间桶，其中"
            f"{sum(1 for item in past if item['candle'])}个形成可追溯势位。"
        ),
        "current": (
            f"当下共有{len(current)}个窗口；{movement_text}。"
            if current else "当下窗口资料不足，暂不形成蜡烛。"
        ),
        "future": (
            f"未来显示{len(future)}个规则推演窗口，可信度随距离按版本化规则递减。"
            if future else "未生成未来窗口；没有以随机插值补齐曲线。"
        ),
        "life_trend_summary": (
            f"有效蜡烛{len(effective)}个，空白窗口"
            f"{sum(1 for item in buckets if item['candle'] is None)}个。"
        ),
        "auspice": labels[state],
        "timing": [
            {
                "window_id": window["window_id"],
                "type": window["type"],
                "start": window["start"],
                "end": window["end"],
                "confidence_bp": window["confidence_bp"],
            }
            for window in result["timing_windows"]
        ],
        "evidence_contracts": support,
        "counterevidence": counters,
        "contested": contested,
        "missing": missing,
        "action_guidance": action,
        "research_status": "sanji_original / research_active / UNCONFIRMED / production_activatable=false",
        "versions": {
            "engine": __version__,
            "ruleset": RULESET_VERSION,
            "evidence_policy": EVIDENCE_POLICY_VERSION,
            "template": REPORT_TEMPLATE_VERSION,
        },
    }
    return structure


def _trace_step(sequence: int, operation: str, parameters: dict) -> dict:
    base = {
        "step_id": f"life-chart:{sequence:03d}:{operation}",
        "sequence": sequence,
        "module_id": "life-chart",
        "operation": operation,
        "input_refs": ["input:life-trend"],
        "rule_refs": [RULESET_VERSION],
        "source_refs": ["SANJI_ORIGINAL_RESEARCH"],
        "parameters": parameters,
        "output_refs": [f"life-chart:{operation}"],
    }
    return {**base, "calculation_hash": content_hash(base)}


def run_life_trend_v1(snapshot: dict) -> tuple[dict, list[dict]]:
    if snapshot.get("operation") != OPERATION:
        raise EngineError(INPUT_INVALID, "life trend operation is not supported")
    unexpected = sorted(
        set(snapshot) - {
            "operation", "profile_id", "subject_id", "as_of", "granularity",
            "start_date", "end_date", "factors", "future_bucket_count",
        }
    )
    if unexpected:
        raise EngineError(INPUT_INVALID, "unexpected life trend input fields", {"fields": unexpected})
    rules = load_life_trend_rules()
    as_of = _parse_as_of(str(snapshot["as_of"]))
    factors = [_normalize_factor(item) for item in snapshot.get("factors", [])]
    factors = sorted(factors, key=lambda item: item["content_hash"])
    known_starts = [
        date.fromisoformat(item["interval_start"]) for item in factors if item["interval_start"]
    ]
    known_ends = [
        date.fromisoformat(item["interval_end"]) for item in factors if item["interval_end"]
    ]
    try:
        start = date.fromisoformat(snapshot.get("start_date") or (
            min(known_starts).isoformat() if known_starts else as_of.isoformat()
        ))
        end = date.fromisoformat(snapshot.get("end_date") or (
            max(max(known_ends, default=as_of), date(as_of.year + 2, 12, 31)).isoformat()
        ))
    except ValueError as exc:
        raise EngineError(INPUT_INVALID, "life trend range is invalid") from exc
    if start > end or (end.year - start.year) > rules["maximum_span_years"]:
        raise EngineError(INPUT_INVALID, "life trend range is invalid or too large")
    granularity = _choose_granularity(
        str(snapshot.get("granularity") or "auto"), factors, start, end
    )
    projection_count = int(snapshot.get("future_bucket_count", 0))
    if not 0 <= projection_count <= rules["maximum_future_bucket_count"]:
        raise EngineError(INPUT_INVALID, "future bucket count exceeds ruleset limit")
    observed_scoring = [
        item for item in factors
        if item["scoring_allowed"]
        and item["epistemic_status"] == "observed"
        and item["interval_end"]
        and date.fromisoformat(item["interval_end"]) <= as_of
    ]
    observed_groups = {item["independence_group"] for item in observed_scoring}
    if projection_count and len(observed_groups) >= 2:
        positive = sum(
            item["magnitude_bp"] for item in observed_scoring
            if item["direction"] == "supports"
        )
        negative = sum(
            item["magnitude_bp"] for item in observed_scoring
            if item["direction"] == "counters"
        )
        direction = "supports" if positive > negative else "counters" if negative > positive else "neutral"
        base_magnitude = min(
            rules["projection_base_cap_bp"],
            abs(positive - negative) // max(1, len(observed_scoring)),
        )
        cursor = _advance(_bucket_interval(_bucket_key(as_of, granularity), granularity)[0], granularity)
        for index in range(projection_count):
            occurred_on, precision = _date_value(cursor, granularity)
            raw = {
                "factor_id": f"projection:{occurred_on}:{index + 1}",
                "factor_type": "projected_trend",
                "factor_kind": "projection",
                "source_system": "life_trend",
                "occurred_on": occurred_on,
                "date_precision": precision,
                "direction": direction,
                "magnitude_bp": (
                    base_magnitude
                    * rules["projection_magnitude_decay_bp"][
                        min(index, len(rules["projection_magnitude_decay_bp"]) - 1)
                    ]
                    // 10_000
                ),
                "source_reliability_bp": 6500,
                "mapping_reliability_bp": 6000,
                "independence_group": f"projection:{occurred_on}",
                "shared_source_group": f"projection:{occurred_on}",
                "epistemic_status": "rule_inferred",
                "rule_id": "LIFE_TREND.PROJECTION.CARRY_DECAY.V1",
                "rule_version": rules["version"],
                "tags": ["projected_future"],
                "source_refs": sorted(item["factor_id"] for item in observed_scoring),
            }
            factors.append(_normalize_factor(raw))
            cursor = _advance(cursor, granularity)
        factors = sorted(factors, key=lambda item: item["content_hash"])
    effective, deduplication = _deduplicate(factors)
    unallocated = [
        item["factor_id"] for item in effective
        if item["interval_start"] and not _supports_precision(item["date_precision"], granularity)
    ]
    allocated: dict[str, list[dict]] = {}
    for factor in effective:
        if not factor["interval_start"] or factor["factor_id"] in unallocated:
            continue
        key = _bucket_key(date.fromisoformat(factor["interval_start"]), granularity)
        allocated.setdefault(key, []).append(factor)
    keys = []
    cursor = _bucket_interval(_bucket_key(start, granularity), granularity)[0]
    end_key = _bucket_key(end, granularity)
    while True:
        key = _bucket_key(cursor, granularity)
        keys.append(key)
        if key == end_key:
            break
        cursor = _advance(cursor, granularity)
        if len(keys) > rules["maximum_bucket_count"]:
            raise EngineError(INPUT_INVALID, "life trend bucket count exceeds ruleset limit")
    buckets, position = [], 0
    return_schedule = rules["diminishing_returns_bp"]
    current_key = _bucket_key(as_of, granularity)
    future_distance = 0
    for index, key in enumerate(keys):
        bucket_start, bucket_end, precision = _bucket_interval(key, granularity)
        items = sorted(
            allocated.get(key, []),
            key=lambda item: (
                item["interval_start"] or "",
                item["factor_id"],
                item["content_hash"],
            ),
        )
        segment = _segment(bucket_start, bucket_end, as_of, bool(items))
        if key > current_key:
            segment = "projected_future" if items else "insufficient_gap"
            future_distance += 1
        confidence, coverage = _confidence(items, segment, future_distance, rules)
        scoring = [item for item in items if item["scoring_allowed"]]
        support = [item for item in scoring if item["direction"] == "supports"]
        counters = [item for item in scoring if item["direction"] == "counters"]
        temporal_groups: dict[tuple[str, str, str], list[dict]] = {}
        for factor in scoring:
            temporal_groups.setdefault(
                (
                    factor["interval_start"] or "",
                    factor["interval_end"] or "",
                    factor["date_precision"],
                ),
                [],
            ).append(factor)
        ordered = [
            factor
            for temporal_key in sorted(temporal_groups)
            for factor in sorted(
                temporal_groups[temporal_key],
                key=lambda item: (
                    -(
                        item["magnitude_bp"]
                        * item["source_reliability_bp"]
                        * item["mapping_reliability_bp"]
                    ),
                    item["direction"],
                    item["content_hash"],
                ),
            )
        ]
        open_value, high_value, low_value = position, position, position
        return_index = 0
        for temporal_key in sorted(temporal_groups):
            group_start = position
            positive_total = 0
            negative_total = 0
            simultaneous = sorted(
                temporal_groups[temporal_key],
                key=lambda item: (
                    -(
                        item["magnitude_bp"]
                        * item["source_reliability_bp"]
                        * item["mapping_reliability_bp"]
                    ),
                    item["direction"],
                    item["content_hash"],
                ),
            )
            for factor in simultaneous:
                delta = _factor_delta(
                    factor,
                    return_schedule[min(return_index, len(return_schedule) - 1)],
                    rules["single_factor_cap_bp"],
                )
                return_index += 1
                if delta >= 0:
                    positive_total += delta
                else:
                    negative_total += delta
            # No evidenced sequence exists inside one canonical interval.
            # Compute directional extrema around the same opening position.
            high_value = max(high_value, _clamp(group_start + positive_total))
            low_value = min(low_value, _clamp(group_start + negative_total))
            position = _clamp(group_start + positive_total + negative_total)
        candle = None
        if scoring:
            candle = {
                "open": open_value,
                "high": high_value,
                "low": low_value,
                "close": position,
            }
        else:
            position = open_value
        bucket = {
            "bucket_id": key,
            "stable_order": index,
            "start": key if precision != "exact_date" else bucket_start.isoformat(),
            "end": key if precision != "exact_date" else bucket_end.isoformat(),
            "time_precision": precision,
            "segment": segment,
            "candle": candle,
            "confidence_bp": confidence,
            "coverage_bp": coverage,
            "support_count": len(support),
            "counter_count": len(counters),
            "conflict_count": sum(item["conflict"] for item in items),
            "driver_factor_ids": [item["factor_id"] for item in ordered],
            "supporting_factor_ids": [item["factor_id"] for item in support],
            "counterevidence_factor_ids": [item["factor_id"] for item in counters],
            "tags": sorted({tag for item in items for tag in item["tags"]}),
            "missing": (
                ["no_allocated_evidence"] if not items else
                ["no_scoring_evidence"] if not scoring else []
            ),
            "trace_ref": f"trace:bucket:{key}",
            "open_policy": rules["gap_open_policy"],
            "simultaneous_factor_policy": rules["simultaneous_factor_policy"],
        }
        bucket["status"] = _bucket_status(bucket, rules)
        bucket["auspice"] = _auspice(bucket, rules)
        bucket["content_hash"] = content_hash(bucket)
        buckets.append(bucket)
    timing = [
        _timing_window(bucket) for bucket in buckets
        if bucket["candle"] is not None or bucket["segment"] == "current_state"
    ]
    core = {
        "schema_version": "life-trend-result/1.0.0",
        "tradition_scope": "sanji_original",
        "activation": "research_active",
        "review_status": "UNCONFIRMED",
        "production_activatable": False,
        "engine_version": __version__,
        "ruleset_version": RULESET_VERSION,
        "ruleset_hash": rules["content_hash"],
        "evidence_policy_version": EVIDENCE_POLICY_VERSION,
        "report_template_version": REPORT_TEMPLATE_VERSION,
        "profile_id": str(snapshot.get("profile_id") or ""),
        "subject_id": str(snapshot.get("subject_id") or snapshot.get("profile_id") or ""),
        "as_of": snapshot["as_of"],
        "granularity": granularity,
        "timeline_segments": [
            "observed_past", "current_state", "projected_future", "insufficient_gap"
        ],
        "factors": factors,
        "effective_factor_ids": [item["factor_id"] for item in effective],
        "deduplication": deduplication,
        "unallocated_factor_ids": sorted(unallocated),
        "buckets": buckets,
        "timing_windows": timing,
        "position_scale": {"internal": [-10_000, 10_000], "display": [-100, 100]},
        "evidence_density_label": "证据密度",
        "no_interpolation": True,
        "no_llm_or_oracle_core_input": True,
    }
    core["report_structure"] = _report_text(core, rules)
    core_projection = deepcopy(core)
    core["core_output_hash"] = content_hash(core_projection)
    deterministic_report = {
        **deepcopy(core["report_structure"]),
        "core_output_hash": core["core_output_hash"],
    }
    core["deterministic_report"] = deterministic_report
    core["deterministic_report_hash"] = content_hash(deterministic_report)
    narrative_input = {
        "schema_version": "life-trend-narrative-input/1.0.0",
        "core_output_hash": core["core_output_hash"],
        "report_outline": deterministic_report,
        "locked_timeline": [
            {
                "bucket_id": bucket["bucket_id"],
                "segment": bucket["segment"],
                "candle": bucket["candle"],
                "confidence_bp": bucket["confidence_bp"],
                "auspice": bucket["auspice"]["state"],
            }
            for bucket in buckets
        ],
        "locked_timing_windows": timing,
        "allowed_names": sorted({
            str(item.get("value"))
            for factor in factors
            for item in factor.get("protected_entities", [])
            if isinstance(item, dict) and item.get("value")
        }),
        "protected_entities": sorted(
            {
                item["display_value"]
                for factor in factors
                for item in factor.get("protected_entities", [])
            }
        ),
        "epistemic_suffixes": ["【可能】", "【相争】", "【可能·资料不足】"],
    }
    core["narrative_input"] = narrative_input
    core["narrative_input_hash"] = content_hash(narrative_input)
    trace = [
        _trace_step(100, "normalize_and_deduplicate_factors", {
            "factor_hashes": [item["content_hash"] for item in factors],
            "deduplication": deduplication,
        }),
        _trace_step(200, "select_time_buckets", {
            "granularity": granularity,
            "keys": keys,
            "unallocated_factor_ids": sorted(unallocated),
        }),
        _trace_step(300, "calculate_integer_ohlc", {
            "bucket_hashes": [item["content_hash"] for item in buckets],
            "gap_open_policy": rules["gap_open_policy"],
            "simultaneous_factor_policy": rules["simultaneous_factor_policy"],
        }),
        _trace_step(400, "derive_auspice_and_timing", {
            "auspice": [item["auspice"] for item in buckets],
            "timing_windows": timing,
        }),
        _trace_step(500, "render_deterministic_report", {
            "core_output_hash": core["core_output_hash"],
            "deterministic_report_hash": core["deterministic_report_hash"],
            "narrative_input_hash": core["narrative_input_hash"],
        }),
    ]
    core["trace_hash"] = content_hash(trace)
    core["result_hash"] = content_hash({
        "core_output_hash": core["core_output_hash"],
        "deterministic_report_hash": core["deterministic_report_hash"],
        "narrative_input_hash": core["narrative_input_hash"],
        "trace_hash": core["trace_hash"],
    })
    return core, trace
