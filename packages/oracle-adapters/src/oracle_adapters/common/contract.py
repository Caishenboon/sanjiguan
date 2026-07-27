from __future__ import annotations

import hashlib
import importlib
import json
from copy import deepcopy
from datetime import datetime
from typing import Any

ORACLE_DEFINITIONS = {
    "bazi.lunar_python": {
        "oracle_version": "1.4.8",
        "upstream_repository": "https://github.com/6tail/lunar-python",
        "upstream_commit": "000c8a3d74eed098d6256a28fdd51b869324c559",
        "license": "MIT",
        "adapter": "oracle_adapters.bazi.lunar_python.adapter",
        "domain": "bazi",
        "ci_allowed": True,
        "production_allowed": False,
    },
    "bazi.tyme4py": {
        "oracle_version": "1.5.0",
        "upstream_repository": "https://github.com/6tail/tyme4py",
        "upstream_commit": "0ad0b416b6b9562f893921e3868b86e2bc68400b",
        "license": "MIT",
        "adapter": "oracle_adapters.bazi.tyme4py.adapter",
        "domain": "bazi",
        "ci_allowed": True,
        "production_allowed": False,
    },
    "bazi.sxtwl": {
        "oracle_version": "2.0.7",
        "upstream_repository": "https://github.com/yuangu/sxtwl_cpp",
        "upstream_commit": "pypi-release-2.0.7",
        "license": "BSD-3-Clause",
        "adapter": "oracle_adapters.bazi.sxtwl.adapter",
        "domain": "bazi",
        "ci_allowed": True,
        "production_allowed": False,
    },
    "ziwei.iztro": {
        "oracle_version": "2.5.8",
        "upstream_repository": "https://github.com/SylarLong/iztro",
        "upstream_commit": "9d39f17",
        "license": "MIT",
        "adapter": "oracle_adapters.ziwei.iztro.adapter",
        "domain": "ziwei",
        "ci_allowed": True,
        "production_allowed": False,
    },
}

DIFF_STATUSES = {
    "exact_match",
    "normalized_match",
    "profile_difference",
    "unsupported",
    "external_error",
    "engine_suspect",
    "oracle_suspect",
    "manual_review_required",
}


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def identify_oracle(oracle_id: str) -> dict:
    if oracle_id not in ORACLE_DEFINITIONS:
        raise ValueError(f"unknown oracle_id: {oracle_id}")
    definition = deepcopy(ORACLE_DEFINITIONS[oracle_id])
    return {"oracle_id": oracle_id, **definition}


def inspect_oracle(oracle_id: str) -> dict:
    definition = identify_oracle(oracle_id)
    definition.pop("adapter", None)
    return {
        **definition,
        "touches_user_data": False,
        "input_policy": "synthetic_or_explicitly_approved_research_input_only",
        "result_role": "differential_evidence_only",
        "affects_engine_determinism": False,
    }


def validate_oracle_input(oracle_id: str, value: dict) -> dict:
    definition = identify_oracle(oracle_id)
    if not isinstance(value, dict):
        raise ValueError("oracle input must be an object")
    if definition["domain"] == "bazi":
        required = {"local_date", "local_time", "profile_id"}
        missing = sorted(required - value.keys())
        if missing:
            raise ValueError(f"missing bazi oracle fields: {missing}")
        if value["local_time"] is not None:
            datetime.fromisoformat(f"{value['local_date']}T{value['local_time']}")
        if value["profile_id"] not in {
            "BAZI.PROFILE.CIVIL_MIDNIGHT.CANDIDATE.V1",
            "BAZI.PROFILE.APPARENT_ZICHU.CANDIDATE.V1",
            "BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1",
        }:
            raise ValueError("unknown bazi profile")
        if value.get("time_resolution_status") not in {None, "resolved", "ambiguous", "nonexistent"}:
            raise ValueError("unknown time_resolution_status")
    else:
        required = {
            "lunar_year",
            "lunar_month",
            "lunar_day",
            "hour_index",
            "traditional_sex",
            "profile_id",
        }
        missing = sorted(required - value.keys())
        if missing:
            raise ValueError(f"missing ziwei oracle fields: {missing}")
        if value["traditional_sex"] not in {"male", "female"}:
            raise ValueError("traditional_sex must be male or female")
    return deepcopy(value)


def normalize_oracle_output(oracle_id: str, raw: dict) -> dict:
    module = importlib.import_module(identify_oracle(oracle_id)["adapter"])
    return module.normalize(raw)


def execute_oracle(oracle_id: str, value: dict) -> dict:
    definition = identify_oracle(oracle_id)
    validated = validate_oracle_input(oracle_id, value)
    summary = {
        key: validated.get(key)
        for key in (
            "local_date",
            "local_time",
            "profile_id",
            "lunar_year",
            "lunar_month",
            "lunar_day",
            "hour_index",
            "traditional_sex",
            "timezone_id",
            "time_resolution_status",
        )
        if key in validated
    }
    base = {
        "oracle_id": oracle_id,
        "oracle_version": definition["oracle_version"],
        "upstream_repository": definition["upstream_repository"],
        "upstream_commit": definition["upstream_commit"],
        "license": definition["license"],
        "input_summary": summary,
        "touches_user_data": False,
        "ci_allowed": definition["ci_allowed"],
        "production_allowed": definition["production_allowed"],
    }
    if definition["domain"] == "bazi" and validated["local_time"] is None:
        result = {
            **base,
            "normalized_result": {},
            "execution_status": "unsupported",
            "unsupported_features": ["unknown_birth_time"],
            "warnings": ["external BaZi Oracle requires an explicit wall time"],
        }
        return {**result, "result_hash": _canonical_hash(result)}
    if definition["domain"] == "bazi" and validated.get("time_resolution_status") in {
        "ambiguous",
        "nonexistent",
    }:
        feature = f"iana_local_time_{validated['time_resolution_status']}"
        result = {
            **base,
            "normalized_result": {},
            "execution_status": "unsupported",
            "unsupported_features": [feature],
            "warnings": [
                "Oracle adapter will not guess an unresolved IANA local-time mapping"
            ],
        }
        return {**result, "result_hash": _canonical_hash(result)}
    try:
        module = importlib.import_module(definition["adapter"])
        raw = module.execute(validated)
        normalized = module.normalize(raw)
        status = raw.get("execution_status", "success")
        warnings = raw.get("warnings", [])
        unsupported = raw.get("unsupported_features", [])
    except ModuleNotFoundError as exc:
        normalized = {}
        status = "unsupported"
        warnings = [f"optional dependency unavailable: {exc.name}"]
        unsupported = ["oracle_runtime_dependency"]
    except Exception as exc:  # external boundary must be contained
        normalized = {}
        status = "external_error"
        warnings = [f"{type(exc).__name__}: {exc}"]
        unsupported = []
    result = {
        **base,
        "normalized_result": normalized,
        "execution_status": status,
        "unsupported_features": unsupported,
        "warnings": warnings,
    }
    return {**result, "result_hash": _canonical_hash(result)}


def _engine_bazi_projection(engine_result: dict) -> list[dict]:
    domain = engine_result["module_results"]["bazi"]["result"]
    return [
        {
            "candidate_id": candidate["candidate_id"],
            "track_id": candidate["track_id"],
            "pillars": {
                key: candidate["pillars"][key]["ganzhi"]
                for key in ("year", "month", "day", "hour")
            },
        }
        for candidate in domain["candidates"]
    ]


def diff_against_engine(oracle_result: dict, engine_result: dict) -> dict:
    if oracle_result["execution_status"] == "unsupported":
        status = "unsupported"
        reasons = oracle_result["unsupported_features"]
        comparisons = []
    elif oracle_result["execution_status"] != "success":
        status = "external_error"
        reasons = oracle_result["warnings"]
        comparisons = []
    elif oracle_result["oracle_id"].startswith("bazi."):
        oracle_pillars = oracle_result["normalized_result"]["pillars"]
        candidates = _engine_bazi_projection(engine_result)
        comparisons = [
            {
                **candidate,
                "field_matches": {
                    field: candidate["pillars"][field] == oracle_pillars[field]
                    for field in ("year", "month", "day", "hour")
                },
            }
            for candidate in candidates
        ]
        exact = [c for c in comparisons if all(c["field_matches"].values())]
        if oracle_result["unsupported_features"]:
            status = "profile_difference"
            reasons = oracle_result["unsupported_features"]
        elif exact:
            status = "exact_match"
            reasons = ["one_or_more_engine_candidates_match_all_four_pillars"]
        elif oracle_result["input_summary"]["profile_id"].endswith("DUAL_SPLIT_ZI.CANDIDATE.V1"):
            status = "profile_difference"
            reasons = ["oracle_has_no_equivalent_dual_split_zi_profile"]
        else:
            status = "manual_review_required"
            reasons = [
                "method_or_boundary_difference",
                "input_conversion_or_solar_term_difference",
            ]
    else:
        oracle_domain = oracle_result["normalized_result"]
        engine_domain = engine_result["module_results"]["ziwei"]["result"]
        field_matches = {
            "life_palace_branch": oracle_domain.get("life_palace_branch")
            == engine_domain["life_palace"]["branch"],
            "body_palace_branch": oracle_domain.get("body_palace_branch")
            == engine_domain["body_palace"]["branch"],
            "five_element_bureau": oracle_domain.get("five_element_bureau")
            == engine_domain["five_element_bureau"]["name"],
            "fourteen_major_stars": {
                item["name"]: item["branch"]
                for item in oracle_domain.get("palaces", [])
                for item in [
                    {"name": star, "branch": item["branch"]}
                    for star in item.get("major_stars", [])
                ]
            }
            == {
                item["name"]: item["branch"]
                for item in engine_domain["fourteen_major_stars"]
            },
        }
        comparisons = [{"field_matches": field_matches}]
        status = "normalized_match" if all(field_matches.values()) else "manual_review_required"
        reasons = (
            ["normalized_core_fields_and_fourteen_major_stars_match"]
            if status == "normalized_match"
            else [
                "profile_or_leap_month_policy_difference",
                "hour_boundary_or_transformation_table_difference",
            ]
        )
    if status not in DIFF_STATUSES:
        raise AssertionError("invalid diff status")
    diff = {
        "oracle_id": oracle_result["oracle_id"],
        "status": status,
        "reasons": reasons,
        "comparisons": comparisons,
        "oracle_result_hash": oracle_result["result_hash"],
        "engine_output_hash": engine_result.get("output_hash"),
        "affects_engine_result": False,
        "requires_manual_review": status in {
            "engine_suspect",
            "oracle_suspect",
            "manual_review_required",
            "profile_difference",
        },
    }
    return {**diff, "diff_hash": _canonical_hash(diff)}
