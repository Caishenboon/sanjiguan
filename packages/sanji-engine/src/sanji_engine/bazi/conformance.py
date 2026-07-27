"""Deterministic BaZi method-profile validation without pillar calculation."""
from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files

from ..canonical import content_hash

PROFILE_SCHEMA_VERSION = "bazi-method-profile/1.0.0"
REGISTRY_VERSION = "bazi-method-profile-registry/1.0.0"
EVIDENCE_VERSION = "bazi-method-evidence/1.0.0"
CASE_ASSET_VERSION = "bazi-boundary-cases/1.0.0"

POLICY_FIELDS = (
    "calendar_basis",
    "legal_time_policy",
    "solar_time_mode",
    "year_boundary_policy",
    "month_boundary_policy",
    "day_rollover_policy",
    "hour_boundary_policy",
    "boundary_inclusion_policy",
    "historical_calendar_policy",
    "unknown_time_policy",
    "location_precision_policy",
)

PROFILE_FIELDS = {
    "schema_version",
    "profile_id",
    "profile_version",
    "profile_class",
    "status",
    "production_activatable",
    *POLICY_FIELDS,
    "source_claim_ids",
    "review_status",
    "reviewer_requirements",
    "known_disputes",
    "selection_authority",
    "content_hash",
}


class ConformanceError(ValueError):
    """Machine-readable conformance failure."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "details": deepcopy(self.details),
        }


def _asset(path: str) -> dict:
    return json.loads(
        files("sanji_engine").joinpath(f"bazi/assets/{path}").read_text("utf-8")
    )


def _check_content_hash(value: dict, label: str) -> None:
    declared = value.get("content_hash")
    actual = content_hash({key: child for key, child in value.items() if key != "content_hash"})
    if declared != actual:
        raise ConformanceError(
            "ASSET_DRIFT",
            f"{label} content hash mismatch",
            {"declared": declared, "actual": actual},
        )


def _validate_policy(field: str, policy: object) -> None:
    if not isinstance(policy, dict):
        raise ConformanceError("DATA_MISSING", f"{field} must be an object")
    allowed = {
        "policy_id", "decision_status", "selected_option", "options",
        "decision_refs", "notes",
    }
    unexpected = sorted(set(policy) - allowed)
    if unexpected:
        raise ConformanceError(
            "PROFILE_MISMATCH",
            f"{field} contains unsupported fields",
            {"fields": unexpected},
        )
    required = {"policy_id", "decision_status", "selected_option", "options", "decision_refs"}
    missing = sorted(required - set(policy))
    if missing:
        raise ConformanceError(
            "DATA_MISSING", f"{field} is incomplete", {"fields": missing}
        )
    if policy["decision_status"] not in {"FROZEN", "CANDIDATE", "UNCONFIRMED"}:
        raise ConformanceError("PROFILE_MISMATCH", f"{field} has an invalid decision status")
    options = policy["options"]
    if not isinstance(options, list) or not options or len(options) != len(set(options)):
        raise ConformanceError("PROFILE_MISMATCH", f"{field}.options must be unique")
    selected = policy["selected_option"]
    if selected is not None and selected not in options:
        raise ConformanceError(
            "PROFILE_MISMATCH", f"{field}.selected_option is not declared"
        )


def validate_profile(profile: dict) -> dict:
    value = deepcopy(profile)
    unexpected = sorted(set(value) - PROFILE_FIELDS)
    missing = sorted(PROFILE_FIELDS - set(value))
    if unexpected:
        raise ConformanceError(
            "PROFILE_MISMATCH", "profile contains unsupported fields", {"fields": unexpected}
        )
    if missing:
        raise ConformanceError(
            "DATA_MISSING", "profile is incomplete", {"fields": missing}
        )
    if value["schema_version"] != PROFILE_SCHEMA_VERSION:
        raise ConformanceError("PROFILE_MISMATCH", "unsupported profile schema")
    if value["status"] not in {"draft", "review_candidate"}:
        raise ConformanceError("PROFILE_MISMATCH", "profile status is not research-safe")
    if value["production_activatable"] is not False:
        raise ConformanceError(
            "PRODUCTION_GATE", "BaZi method profiles cannot be production-activatable"
        )
    if value["review_status"] not in {"UNCONFIRMED", "PENDING_QUALIFIED_REVIEW"}:
        raise ConformanceError("PROFILE_MISMATCH", "profile review status is invalid")
    if value["selection_authority"] != "CANDIDATE_ONLY_NOT_OWNER_DECISION":
        raise ConformanceError(
            "PRODUCTION_GATE", "profile attempts to claim owner selection authority"
        )
    if not value["source_claim_ids"]:
        raise ConformanceError("DATA_MISSING", "profile has no source claims")
    for field in POLICY_FIELDS:
        _validate_policy(field, value[field])
    _check_content_hash(value, value["profile_id"])
    return value


def _registry() -> dict:
    registry = _asset("profile-registry-1.0.0.json")
    if registry.get("schema_version") != REGISTRY_VERSION:
        raise ConformanceError("ASSET_DRIFT", "unsupported profile registry")
    _check_content_hash(registry, "profile registry")
    return registry


def list_profiles() -> list[dict]:
    registry = _registry()
    return [
        {
            "profile_id": profile_id,
            "filename": definition["filename"],
            "content_hash": definition["content_hash"],
        }
        for profile_id, definition in sorted(registry["profiles"].items())
    ]


def load_profile(profile_id: str) -> dict:
    definition = _registry()["profiles"].get(profile_id)
    if definition is None:
        raise ConformanceError(
            "PROFILE_NOT_FOUND", "unknown BaZi method profile", {"profile_id": profile_id}
        )
    profile = validate_profile(_asset(definition["filename"]))
    if profile["content_hash"] != definition["content_hash"]:
        raise ConformanceError("ASSET_DRIFT", "profile registry hash mismatch")
    return profile


def load_evidence_bundle() -> dict:
    evidence = _asset("method-evidence-1.0.0.json")
    if evidence.get("schema_version") != EVIDENCE_VERSION:
        raise ConformanceError("ASSET_DRIFT", "unsupported evidence asset")
    _check_content_hash(evidence, "method evidence")
    locators = evidence.get("locators")
    claims = evidence.get("claims")
    if not isinstance(locators, list) or not isinstance(claims, list):
        raise ConformanceError("DATA_MISSING", "evidence claims or locators are missing")
    locator_ids = [item["locator_id"] for item in locators]
    claim_ids = [item["claim_id"] for item in claims]
    if len(locator_ids) != len(set(locator_ids)) or len(claim_ids) != len(set(claim_ids)):
        raise ConformanceError("ASSET_DRIFT", "evidence identifiers are not unique")
    known_locators = set(locator_ids)
    known_claims = set(claim_ids)
    locator_fields = {
        "locator_id", "source_id", "source_level", "access_class",
        "location", "tradition_tags",
    }
    claim_fields = {
        "claim_id", "claim_type", "claim", "locator_ids",
        "supports_claim_ids", "contradicts_claim_ids", "review_status",
        "review_candidate_ready", "missing_evidence",
    }
    for locator in locators:
        if set(locator) != locator_fields:
            raise ConformanceError(
                "PROFILE_MISMATCH", "locator shape is not strict",
                {"locator_id": locator.get("locator_id")},
            )
    for claim in claims:
        if set(claim) != claim_fields:
            raise ConformanceError(
                "PROFILE_MISMATCH", "claim shape is not strict",
                {"claim_id": claim.get("claim_id")},
            )
        if not set(claim["locator_ids"]) <= known_locators:
            raise ConformanceError("DATA_MISSING", "claim references an unknown locator")
        for field in ("supports_claim_ids", "contradicts_claim_ids"):
            if not set(claim[field]) <= known_claims:
                raise ConformanceError("DATA_MISSING", f"claim has invalid {field}")
    for definition in _registry()["profiles"].values():
        profile = validate_profile(_asset(definition["filename"]))
        if not set(profile["source_claim_ids"]) <= known_claims:
            raise ConformanceError("DATA_MISSING", "profile references an unknown claim")
    return evidence


def load_boundary_cases() -> dict:
    asset = _asset("boundary-cases-1.0.0.json")
    if asset.get("schema_version") != CASE_ASSET_VERSION:
        raise ConformanceError("ASSET_DRIFT", "unsupported boundary-case asset")
    _check_content_hash(asset, "boundary cases")
    cases = asset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ConformanceError("DATA_MISSING", "boundary cases are missing")
    ids = [item["case_id"] for item in cases]
    if len(ids) != len(set(ids)):
        raise ConformanceError("ASSET_DRIFT", "boundary case identifiers are not unique")
    profile_ids = {item["profile_id"] for item in list_profiles()}
    evidence_claim_ids = {
        item["claim_id"] for item in load_evidence_bundle()["claims"]
    }
    for case in cases:
        expected = {
            "case_id", "classification", "category", "input", "profile_ids",
            "expected_difference", "source_claim_ids", "review_status",
            "formal_gate_eligible", "content_hash",
        }
        if set(case) != expected:
            raise ConformanceError(
                "DATA_MISSING", "boundary case shape is invalid", {"case_id": case.get("case_id")}
            )
        if not set(case["profile_ids"]) <= profile_ids:
            raise ConformanceError("PROFILE_MISMATCH", "case references an unknown profile")
        if not set(case["source_claim_ids"]) <= evidence_claim_ids:
            raise ConformanceError("DATA_MISSING", "case references an unknown claim")
        _check_content_hash(case, case["case_id"])
    return asset


def _policy_projection(profile: dict) -> dict:
    return {
        field: {
            "decision_status": profile[field]["decision_status"],
            "selected_option": profile[field]["selected_option"],
        }
        for field in POLICY_FIELDS
    }


def compare_profiles(profile_ids: list[str]) -> dict:
    if not profile_ids:
        raise ConformanceError("DATA_MISSING", "at least one profile is required")
    if len(profile_ids) != len(set(profile_ids)):
        raise ConformanceError("PROFILE_MISMATCH", "profile identifiers must be unique")
    profiles = [load_profile(profile_id) for profile_id in profile_ids]
    projections = {
        profile["profile_id"]: _policy_projection(profile) for profile in profiles
    }
    differences = {}
    for field in POLICY_FIELDS:
        selections = {
            profile_id: projection[field]["selected_option"]
            for profile_id, projection in projections.items()
        }
        if len(set(selections.values())) > 1:
            differences[field] = selections
    return {
        "profile_ids": profile_ids,
        "profile_hashes": {
            profile["profile_id"]: profile["content_hash"] for profile in profiles
        },
        "differences": differences,
        "pillar_results": None,
        "calculation_performed": False,
    }


def run_conformance(profile_ids: list[str], case_ids: list[str] | None = None) -> dict:
    comparison = compare_profiles(profile_ids)
    asset = load_boundary_cases()
    selected_ids = set(case_ids or [case["case_id"] for case in asset["cases"]])
    known = {case["case_id"] for case in asset["cases"]}
    missing = sorted(selected_ids - known)
    if missing:
        raise ConformanceError(
            "DATA_MISSING", "unknown boundary cases", {"case_ids": missing}
        )
    cases = [
        {
            "case_id": case["case_id"],
            "category": case["category"],
            "classification": case["classification"],
            "expected_difference": case["expected_difference"],
            "case_hash": case["content_hash"],
        }
        for case in asset["cases"]
        if case["case_id"] in selected_ids
    ]
    base = {
        "schema_version": "bazi-conformance-result/1.0.0",
        "status": "method_comparison_only",
        "production_activatable": False,
        "comparison": comparison,
        "cases": cases,
        "boundary_asset_hash": asset["content_hash"],
        "evidence_asset_hash": load_evidence_bundle()["content_hash"],
        "pillar_results": None,
        "calculation_performed": False,
    }
    return {**base, "content_hash": content_hash(base)}
