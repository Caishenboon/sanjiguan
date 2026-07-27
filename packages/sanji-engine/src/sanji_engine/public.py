"""The only supported application-facing API for sanji-engine 1.0."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN

from . import __version__
from .bazi import (
    ConformanceError,
    calculate_four_pillars,
    load_execution_profile,
    load_profile,
)
from .calendar import normalize_birth_time, solar_term_instant
from .canonical import CANONICALIZATION_VERSION, content_hash
from .disabled import disabled_result
from .inference.assets import load_research_assets
from .inference import run_research_baseline
from .errors import (
    EngineError,
    INPUT_INVALID,
    NONDETERMINISTIC_CONTEXT,
    REPLAY_ASSET_MISSING,
    REPLAY_DATA_VERSION_MISMATCH,
    REPLAY_INPUT_MISMATCH,
    REPLAY_METHOD_VERSION_MISMATCH,
    REPLAY_RESULT_MISMATCH,
    RULESET_HASH_MISMATCH,
    RULESET_REVOKED,
    SCHEMA_UNSUPPORTED,
)
from .rulesets import load_bundle
from .yijing import cast_physical_three_coin
from .yijing.assets import ASSET_VERSION as YIJING_ASSET_VERSION
from .ziwei import calculate_chart as calculate_ziwei_chart, load_profile as load_ziwei_profile

__all__ = ["validate_request", "execute", "replay", "inspect_ruleset"]

ENGINE_API_VERSION = "1.0"
REQUEST_SCHEMA_VERSION = "engine-request/1.0.0"
RESULT_SCHEMA_VERSION = "engine-result/1.0.0"
MODULES = {
    "calendar", "bazi", "ziwei", "yijing", "signals", "inference",
    "past-life", "bardo", "relationship", "life-chart",
}


def _require_mapping(value, field: str) -> dict:
    if not isinstance(value, dict):
        raise EngineError(INPUT_INVALID, f"{field} must be an object")
    return value


def _validate_hash_safe(value, path: str = "$") -> None:
    if isinstance(value, float):
        raise EngineError(
            INPUT_INVALID,
            f"{path} contains a binary float; use an explicitly scaled decimal string",
        )
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise EngineError(INPUT_INVALID, f"{path} has a non-string key")
            _validate_hash_safe(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_hash_safe(child, f"{path}[{index}]")
    elif value is not None and not isinstance(value, (str, int, bool)):
        raise EngineError(INPUT_INVALID, f"{path} contains unsupported type")


def validate_request(request: dict) -> dict:
    value = deepcopy(_require_mapping(request, "request"))
    allowed = {
        "schema_version", "engine_api_version", "run_id", "run_mode",
        "requested_modules", "input_snapshot", "ruleset_bundle_id",
        "data_versions", "deterministic_context", "requested_trace_level",
    }
    unexpected = sorted(value.keys() - allowed)
    if unexpected:
        raise EngineError(
            INPUT_INVALID, "unexpected request fields", {"fields": unexpected}
        )
    if value.get("schema_version") != REQUEST_SCHEMA_VERSION:
        raise EngineError(SCHEMA_UNSUPPORTED, "engine request schema version is not supported")
    if value.get("engine_api_version") != ENGINE_API_VERSION:
        raise EngineError(SCHEMA_UNSUPPORTED, "engine API version is not supported")
    required = {
        "run_id", "run_mode", "requested_modules", "input_snapshot",
        "ruleset_bundle_id", "data_versions", "deterministic_context",
    }
    missing = sorted(required - value.keys())
    if missing:
        raise EngineError(INPUT_INVALID, "required request fields are missing", {"fields": missing})
    if value["run_mode"] not in {"research_preview", "replay"}:
        raise EngineError(INPUT_INVALID, "run_mode is not allowed")
    if value.get("requested_trace_level", "full") != "full":
        raise EngineError(INPUT_INVALID, "only full machine-readable trace is supported")
    modules = value["requested_modules"]
    if not isinstance(modules, list) or not modules or len(modules) != len(set(modules)):
        raise EngineError(INPUT_INVALID, "requested_modules must be a non-empty unique list")
    unknown = sorted(set(modules) - MODULES)
    if unknown:
        raise EngineError(INPUT_INVALID, "unknown requested module", {"modules": unknown})
    research_modules = set(modules) & {"signals", "inference"}
    if research_modules and research_modules != {"signals", "inference"}:
        raise EngineError(
            INPUT_INVALID,
            "signals and inference must be requested together for this research baseline",
        )
    if "yijing" in modules and len(modules) != 1:
        raise EngineError(
            INPUT_INVALID,
            "physical three-coin yijing must be requested as an isolated mechanical module",
        )
    context = _require_mapping(value["deterministic_context"], "deterministic_context")
    if context.get("random_method") != "none" or context.get("random_seed") is not None:
        raise EngineError(
            NONDETERMINISTIC_CONTEXT,
            "this Sprint permits no software-random calculation",
        )
    try:
        datetime.fromisoformat(str(context["as_of"]).replace("Z", "+00:00"))
    except (KeyError, ValueError) as exc:
        raise EngineError(INPUT_INVALID, "deterministic_context.as_of is invalid") from exc
    data_versions = _require_mapping(value["data_versions"], "data_versions")
    missing_versions = sorted(
        {"tzdb", "ephemeris", "calendar_dataset"} - data_versions.keys()
    )
    if missing_versions:
        raise EngineError(
            INPUT_INVALID, "data versions are incomplete", {"fields": missing_versions}
        )
    if "yijing" in modules and data_versions.get("yijing_hexagram_mapping") != YIJING_ASSET_VERSION:
        raise EngineError(
            REPLAY_DATA_VERSION_MISMATCH,
            "yijing hexagram mapping data version is unavailable",
        )
    snapshot = _require_mapping(value["input_snapshot"], "input_snapshot")
    if "ziwei" in modules:
        if modules != ["ziwei"] or value["ruleset_bundle_id"] not in {
            "ziwei-sanhe-research-1.0.0",
            "ziwei-sanhe-research-1.0.0-revoked-fixture",
        }:
            raise EngineError(
                INPUT_INVALID,
                "Ziwei research execution must be an isolated module request with its research ruleset",
            )
        profile_id = snapshot.get("profile_id")
        profile_version = snapshot.get("profile_version")
        if not isinstance(profile_id, str) or not isinstance(profile_version, str):
            raise EngineError(
                INPUT_INVALID,
                "Ziwei execution requires explicit profile_id and profile_version; no default is permitted",
            )
        if data_versions.get("ziwei_profiles") != "ziwei-profile-registry/1.0.0":
            raise EngineError(REPLAY_DATA_VERSION_MISMATCH, "Ziwei profile registry version is unavailable")
        if data_versions.get("ziwei_transformations") != "birth-year-transformations-candidate/1.0.0":
            raise EngineError(REPLAY_DATA_VERSION_MISMATCH, "Ziwei transformation asset version is unavailable")
        if data_versions.get("ziwei_source_claims") != "ziwei-source-claim-registry/1.0.0":
            raise EngineError(REPLAY_DATA_VERSION_MISMATCH, "Ziwei source-claim asset version is unavailable")
        load_ziwei_profile(profile_id, profile_version)
    if "bazi" in modules:
        executable = value["ruleset_bundle_id"] == "bazi-four-pillars-research-1.0.0"
        if executable and modules != ["bazi"]:
            raise EngineError(
                INPUT_INVALID,
                "BaZi four-pillar research execution must be an isolated module request",
            )
        profile_id = (
            snapshot.get("profile_id") if executable
            else snapshot.get("bazi_method_profile_id")
        )
        if not isinstance(profile_id, str) or not profile_id:
            raise EngineError(
                INPUT_INVALID,
                "bazi execution requires an explicit method profile; no default is permitted",
            )
        expected_registry = (
            "bazi-execution-profiles/1.0.0" if executable
            else "bazi-method-profile-registry/1.0.0"
        )
        if data_versions.get("bazi_method_profiles") != expected_registry:
            raise EngineError(
                REPLAY_DATA_VERSION_MISMATCH,
                "bazi method-profile registry version is unavailable",
            )
        try:
            if executable:
                profile_version = snapshot.get("profile_version")
                if not isinstance(profile_version, str) or not profile_version:
                    raise EngineError(
                        INPUT_INVALID,
                        "bazi execution requires explicit profile_id and profile_version",
                    )
                for field, expected in {
                    "bazi_day_epoch": "bazi-day-epoch/1.0.0",
                    "bazi_boundary_cases": "bazi-boundary-cases/1.0.0",
                    "solar_terms": "astronomy-engine/2.1.19",
                }.items():
                    if data_versions.get(field) != expected:
                        raise EngineError(
                            REPLAY_DATA_VERSION_MISMATCH,
                            f"BaZi data version is unavailable: {field}",
                        )
                load_execution_profile(profile_id, profile_version)
            else:
                load_profile(profile_id)
        except ConformanceError as exc:
            raise EngineError(
                INPUT_INVALID,
                "bazi method profile failed conformance",
                exc.as_dict(),
            ) from exc
    _validate_hash_safe(value)
    bundle = inspect_ruleset(value["ruleset_bundle_id"])
    if bundle.get("status") == "revoked_for_future_runs" and value["run_mode"] != "replay":
        raise EngineError(
            RULESET_REVOKED,
            "revoked ruleset is available only for historical replay",
        )
    return value


def inspect_ruleset(bundle_id: str) -> dict:
    return deepcopy(load_bundle(bundle_id))


def _scaled(value: float | None) -> str | None:
    if value is None:
        return None
    return format(
        Decimal(str(value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN),
        "f",
    )


def _calendar_hash_safe(result: dict) -> dict:
    safe = deepcopy(result)
    for key in (
        "longitude_correction_minutes",
        "equation_of_time_minutes",
        "total_apparent_correction_minutes",
    ):
        safe[key] = _scaled(safe[key])
    for step in safe["correction_chain"]:
        step["offset_minutes"] = _scaled(step["offset_minutes"])
    place = safe["original"]["place"]
    place["latitude"] = str(place["latitude"])
    place["longitude"] = str(place["longitude"])
    return safe


def _research_hash_safe(value):
    """Encode legacy float values as exact decimal strings at the JCS boundary."""
    if isinstance(value, float):
        return str(value)
    if isinstance(value, dict):
        return {key: _research_hash_safe(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_research_hash_safe(child) for child in value]
    return value


def _trace_step(sequence: int, operation: str, input_ref: str, output_ref: str) -> dict:
    step = {
        "step_id": f"calendar:{sequence:03d}:{operation}",
        "sequence": sequence,
        "module_id": "calendar",
        "operation": operation,
        "input_refs": [input_ref],
        "rule_refs": ["CALENDAR.MIGRATION.BASELINE.V1"],
        "source_refs": [
            "IANA_TZDB",
            "NOAA_GENERAL_SOLAR_POSITION_CALCULATIONS",
            "ASTRONOMY_ENGINE_PINNED",
        ],
        "parameters": {},
        "output_refs": [output_ref],
    }
    return {**step, "calculation_hash": content_hash(step)}


def _execute_calendar(snapshot: dict) -> tuple[dict, list[dict]]:
    operation = snapshot.get("operation")
    if operation == "normalize_birth_time":
        record = _require_mapping(snapshot.get("birth_record"), "birth_record")
        terms = [
            datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            for value in snapshot.get("solar_term_instants_utc", [])
        ]
        result = _calendar_hash_safe(normalize_birth_time(record, terms))
        trace = [
            _trace_step(10, "civil_time_normalization", "input:birth_record", "calendar:civil"),
            _trace_step(20, "local_mean_solar_correction", "calendar:civil", "calendar:mean"),
            _trace_step(30, "equation_of_time_correction", "calendar:mean", "calendar:apparent"),
            _trace_step(40, "boundary_difference_detection", "calendar:candidates", "calendar:boundaries"),
        ]
    elif operation == "solar_term_instant":
        instant = solar_term_instant(
            int(snapshot["target_longitude"]),
            datetime.fromisoformat(snapshot["search_start_utc"].replace("Z", "+00:00")),
            float(snapshot.get("limit_days", "20")),
        )
        result = {
            "target_longitude": int(snapshot["target_longitude"]),
            "instant_utc": instant.isoformat(),
            "method_id": "CALENDAR.SOLAR_TERM.ASTRONOMY_ENGINE.V1",
        }
        trace = [
            _trace_step(
                10, "search_solar_longitude", "input:solar_term_search", "calendar:solar_term"
            )
        ]
    else:
        raise EngineError(INPUT_INVALID, "calendar operation is not supported")
    module = {
        "module_id": "calendar",
        "module_version": "0.1.0",
        "method_id": "CALENDAR.MIGRATION.BASELINE.V1",
        "method_status": "research_active",
        "result": result,
        "trace_step_ids": [step["step_id"] for step in trace],
        "rule_refs": ["CALENDAR.MIGRATION.BASELINE.V1"],
        "source_refs": [
            "IANA_TZDB",
            "NOAA_GENERAL_SOLAR_POSITION_CALCULATIONS",
            "ASTRONOMY_ENGINE_PINNED",
        ],
        "uncertainties": [],
        "sensitivity_flags": result.get("boundary_difference", {}).get(
            "sensitive_rules", []
        ),
    }
    return {**module, "content_hash": content_hash(module)}, trace


def _research_trace_step(
    sequence: int,
    module_id: str,
    operation: str,
    parameters: dict,
    input_refs: list[str],
    output_refs: list[str],
) -> dict:
    step = {
        "step_id": f"{module_id}:{sequence:03d}:{operation}",
        "sequence": sequence,
        "module_id": module_id,
        "operation": operation,
        "input_refs": input_refs,
        "rule_refs": [
            "SIGNALS.RESEARCH_BASELINE.0.1.0",
            "INFERENCE.RESEARCH_BASELINE.0.1.0",
        ],
        "source_refs": ["SANJI_RESEARCH_BASELINE_SYNTHETIC"],
        "parameters": _research_hash_safe(parameters),
        "output_refs": output_refs,
    }
    return {**step, "calculation_hash": content_hash(step)}


def _restore_research_case(snapshot: dict) -> dict:
    if snapshot.get("operation") != "run_research_inference":
        raise EngineError(INPUT_INVALID, "research inference operation is not supported")
    case = deepcopy(_require_mapping(snapshot.get("case"), "case"))
    for field in ("completeness",):
        if field in case:
            case[field] = float(case[field])
    for signal in case.get("signals", []):
        for field in ("strength", "source_reliability", "relevance"):
            if field in signal:
                signal[field] = float(signal[field])
    return case


def _execute_research(snapshot: dict) -> tuple[dict[str, dict], list[dict], dict]:
    case = _restore_research_case(snapshot)
    archetypes, config, asset_hashes = load_research_assets()
    actual = run_research_baseline(case, archetypes, config)
    safe_signals = _research_hash_safe(actual["signals"])
    safe_weights = _research_hash_safe(actual["weights"])
    safe_locked = _research_hash_safe(actual["locked_verdict"])
    safe_research_trace = _research_hash_safe(actual["research_trace"])
    signals_result = {
        "signals": safe_signals,
        "weights": safe_weights,
        "legacy_input_hash": actual["input_hash"],
        "deduplication": safe_research_trace["deduplication"],
        "asset_hashes": asset_hashes,
    }
    inference_result = {
        "locked_verdict": safe_locked,
        "legacy_locked_hash": actual["locked_hash"],
        "legacy_stages": actual["stages"],
        "candidate_generation": safe_research_trace["candidate_generation"],
        "research_trace": safe_research_trace,
        "asset_hashes": asset_hashes,
    }
    trace = [
        _research_trace_step(
            100,
            "signals",
            "validate_and_deduplicate_signals",
            {
                "signals": safe_signals,
                "deduplication": safe_research_trace["deduplication"],
            },
            ["input:case.signals"],
            ["signals:normalized"],
        ),
        _research_trace_step(
            200,
            "inference",
            "generate_and_score_candidates",
            {
                "candidate_generation": safe_research_trace["candidate_generation"],
                "candidate_contributions": safe_research_trace[
                    "candidate_contributions"
                ],
            },
            ["signals:normalized", "ruleset:research-baseline-0.2.0"],
            ["inference:scored_candidates"],
        ),
        _research_trace_step(
            300,
            "inference",
            "rank_and_decide_status",
            {
                "status_decision": safe_research_trace["status_decision"],
                "ranked_ids": [
                    item["id"] for item in safe_locked["ranked_hypotheses"]
                ],
            },
            ["inference:scored_candidates"],
            ["inference:locked_verdict"],
        ),
    ]
    definitions = {
        "signals": {
            "method_id": "SIGNALS.RESEARCH_BASELINE.0.1.0",
            "result": signals_result,
        },
        "inference": {
            "method_id": "INFERENCE.RESEARCH_BASELINE.0.1.0",
            "result": inference_result,
        },
    }
    module_results = {}
    for module_id, definition in definitions.items():
        module = {
            "module_id": module_id,
            "module_version": "0.2.0",
            "method_id": definition["method_id"],
            "method_status": "research_baseline",
            "production_activatable": False,
            "result": definition["result"],
            "trace_step_ids": [
                step["step_id"] for step in trace if step["module_id"] == module_id
            ],
            "rule_refs": [definition["method_id"]],
            "source_refs": ["SANJI_RESEARCH_BASELINE_SYNTHETIC"],
            "uncertainties": [
                "THEORY_UNVALIDATED",
                "LEGACY_BINARY_FLOAT_COMPATIBILITY",
            ],
            "sensitivity_flags": [],
        }
        module_results[module_id] = {
            **module,
            "content_hash": content_hash(module),
        }
    domain_projection = {
        "signals": safe_signals,
        "weights": safe_weights,
        "locked_verdict": safe_locked,
        "legacy_locked_hash": actual["locked_hash"],
    }
    return module_results, trace, {
        "research_domain_hash": content_hash(domain_projection),
        "legacy_locked_hash": actual["locked_hash"],
    }


def execute(request: dict) -> dict:
    validated = validate_request(request)
    bundle = inspect_ruleset(validated["ruleset_bundle_id"])
    input_projection = deepcopy(validated)
    input_projection.pop("run_id", None)
    # Execution and replay are transport intents, not calculation inputs. Excluding
    # run_mode lets a replay prove equivalence with the original research run.
    input_projection.pop("run_mode", None)
    input_hash = content_hash(input_projection)
    module_results: dict[str, dict] = {}
    trace: list[dict] = []
    disabled_modules: list[str] = []
    research_metadata: dict = {}
    yijing_metadata: dict = {}
    bazi_metadata: dict = {}
    ziwei_metadata: dict = {}
    research_requested = {"signals", "inference"} <= set(
        validated["requested_modules"]
    )
    research_results: dict[str, dict] = {}
    if research_requested:
        research_results, research_trace, research_metadata = _execute_research(
            validated["input_snapshot"]
        )
        trace.extend(research_trace)
    yijing_result = None
    if "yijing" in validated["requested_modules"]:
        definition = bundle["modules"]["yijing"]
        if definition["enabled"]:
            result, yijing_trace, yijing_metadata = cast_physical_three_coin(
                validated["input_snapshot"]
            )
            result["ruleset_id"] = bundle["bundle_id"]
            result["ruleset_status"] = bundle["status"]
            yijing_metadata["yijing_domain_hash"] = content_hash(result)
            module = {
                "module_id": "yijing",
                "module_version": "0.1.0",
                "method_id": definition["method_id"],
                "method_status": "traditional_mechanical",
                "production_activatable": False,
                "result": result,
                "trace_step_ids": [step["step_id"] for step in yijing_trace],
                "rule_refs": [definition["method_id"]],
                "source_refs": definition["source_ids"],
                "uncertainties": ["INTERPRETATION_OUT_OF_SCOPE"],
                "sensitivity_flags": [],
            }
            yijing_result = {**module, "content_hash": content_hash(module)}
            trace.extend(yijing_trace)
    bazi_result = None
    if "bazi" in validated["requested_modules"]:
        definition = bundle["modules"]["bazi"]
        if definition["enabled"]:
            result, bazi_trace, bazi_metadata = calculate_four_pillars(
                validated["input_snapshot"]
            )
            module = {
                "module_id": "bazi",
                "module_version": "1.0.0",
                "method_id": definition["method_id"],
                "method_status": "traditional_mechanical_research_candidate",
                "production_activatable": False,
                "result": result,
                "trace_step_ids": [step["step_id"] for step in bazi_trace],
                "rule_refs": [definition["method_id"]],
                "source_refs": definition["source_ids"],
                "uncertainties": [
                    "D002_UNCONFIRMED",
                    "D003_UNCONFIRMED",
                    "SOURCE_ATTESTATION_PENDING",
                ],
                "sensitivity_flags": sorted({
                    flag
                    for candidate in result["candidates"]
                    for flag, active in candidate["boundary_flags"].items()
                    if active
                }),
            }
            bazi_result = {**module, "content_hash": content_hash(module)}
            trace.extend(bazi_trace)
    ziwei_result = None
    if "ziwei" in validated["requested_modules"]:
        definition = bundle["modules"]["ziwei"]
        if definition["enabled"]:
            result, ziwei_trace, ziwei_metadata = calculate_ziwei_chart(
                validated["input_snapshot"]
            )
            module = {
                "module_id": "ziwei",
                "module_version": "1.0.0",
                "method_id": definition["method_id"],
                "method_status": "traditional_mechanical",
                "production_activatable": False,
                "result": result,
                "trace_step_ids": [step["step_id"] for step in ziwei_trace],
                "rule_refs": [definition["method_id"]],
                "source_refs": definition["source_ids"],
                "uncertainties": [
                    "D005_UNCONFIRMED",
                    "FOUR_TRANSFORMATIONS_SOURCE_REVIEW_PENDING",
                ],
                "sensitivity_flags": [
                    result["leap_month_decision"]
                    if result["lunar_birth"]["is_leap_month"] else "none"
                ],
            }
            ziwei_result = {**module, "content_hash": content_hash(module)}
            trace.extend(ziwei_trace)
    for module_id in validated["requested_modules"]:
        definition = bundle["modules"][module_id]
        if module_id == "calendar" and definition["enabled"]:
            module_results[module_id], module_trace = _execute_calendar(
                validated["input_snapshot"]
            )
            trace.extend(module_trace)
        elif module_id in research_results and definition["enabled"]:
            module_results[module_id] = research_results[module_id]
        elif module_id == "yijing" and yijing_result is not None:
            module_results[module_id] = yijing_result
        elif module_id == "bazi" and bazi_result is not None:
            module_results[module_id] = bazi_result
        elif module_id == "ziwei" and ziwei_result is not None:
            module_results[module_id] = ziwei_result
        else:
            module_results[module_id] = disabled_result(module_id, definition)
            disabled_modules.append(module_id)
    trace_hash = content_hash(trace)
    manifest_base = {
        "schema_version": "replay-manifest/1.0.0",
        "engine_version": __version__,
        "engine_api_version": ENGINE_API_VERSION,
        "canonicalization_version": CANONICALIZATION_VERSION,
        "ruleset_bundle_id": bundle["bundle_id"],
        "ruleset_bundle_hash": bundle["bundle_hash"],
        "data_versions": validated["data_versions"],
        "input_hash": input_hash,
        "trace_hash": trace_hash,
        "random_context": validated["deterministic_context"],
    }
    if research_requested:
        manifest_base["method_versions"] = {
            "signals": bundle["modules"]["signals"]["method_id"],
            "inference": bundle["modules"]["inference"]["method_id"],
        }
        manifest_base["domain_result_hashes"] = research_metadata
    if yijing_result is not None:
        manifest_base["method_versions"] = {
            "yijing": bundle["modules"]["yijing"]["method_id"],
        }
        manifest_base["domain_result_hashes"] = yijing_metadata
    if bazi_result is not None:
        manifest_base["method_versions"] = {
            "bazi": bundle["modules"]["bazi"]["method_id"],
        }
        manifest_base["domain_result_hashes"] = bazi_metadata
    if ziwei_result is not None:
        manifest_base["method_versions"] = {
            "ziwei": bundle["modules"]["ziwei"]["method_id"],
        }
        manifest_base["domain_result_hashes"] = ziwei_metadata
    replay_manifest = {
        **manifest_base,
        "content_hash": content_hash(manifest_base),
    }
    result_base = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "engine_api_version": ENGINE_API_VERSION,
        "engine_version": __version__,
        "run_id": validated["run_id"],
        "ruleset_bundle_id": bundle["bundle_id"],
        "ruleset_bundle_hash": bundle["bundle_hash"],
        "input_hash": input_hash,
        "status": "complete_with_disabled_modules" if disabled_modules else "complete",
        "module_results": module_results,
        "trace": trace,
        "trace_hash": trace_hash,
        "replay_manifest": replay_manifest,
        "disabled_modules": disabled_modules,
        "warnings": [],
    }
    output_projection = deepcopy(result_base)
    output_projection.pop("run_id", None)
    return {**result_base, "output_hash": content_hash(output_projection)}


def replay(manifest: dict, request: dict) -> dict:
    manifest = deepcopy(_require_mapping(manifest, "manifest"))
    required = {
        "schema_version", "engine_version", "engine_api_version",
        "ruleset_bundle_id", "ruleset_bundle_hash", "data_versions",
        "input_hash", "trace_hash", "random_context", "content_hash",
    }
    if required - manifest.keys():
        raise EngineError(REPLAY_ASSET_MISSING, "replay manifest is incomplete")
    expected_manifest_hash = content_hash(
        {key: value for key, value in manifest.items() if key != "content_hash"}
    )
    if manifest["content_hash"] != expected_manifest_hash:
        raise EngineError(RULESET_HASH_MISMATCH, "replay manifest hash mismatch")
    bundle = inspect_ruleset(manifest["ruleset_bundle_id"])
    if bundle["bundle_hash"] != manifest["ruleset_bundle_hash"]:
        raise EngineError(RULESET_HASH_MISMATCH, "ruleset bundle hash mismatch")
    if request.get("data_versions") != manifest["data_versions"]:
        raise EngineError(
            REPLAY_DATA_VERSION_MISMATCH, "replay data versions do not match"
        )
    if "method_versions" in manifest:
        current_methods = {
            module_id: bundle["modules"][module_id]["method_id"]
            for module_id in manifest["method_versions"]
        }
        if current_methods != manifest["method_versions"]:
            raise EngineError(
                REPLAY_METHOD_VERSION_MISMATCH,
                "replay method versions do not match",
            )
    replay_request = deepcopy(request)
    replay_request["run_mode"] = "replay"
    result = execute(replay_request)
    if result["input_hash"] != manifest["input_hash"]:
        raise EngineError(REPLAY_INPUT_MISMATCH, "replay input hash mismatch")
    if result["trace_hash"] != manifest["trace_hash"]:
        raise EngineError(REPLAY_RESULT_MISMATCH, "replay trace hash mismatch")
    if (
        "domain_result_hashes" in manifest
        and result["replay_manifest"].get("domain_result_hashes")
        != manifest["domain_result_hashes"]
    ):
        raise EngineError(REPLAY_RESULT_MISMATCH, "replay domain result mismatch")
    return result
