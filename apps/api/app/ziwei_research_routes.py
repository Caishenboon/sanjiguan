"""Owner-only adapter for Ziwei engine execution and isolated Oracle diffs."""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Body, Cookie, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sanji_engine import execute

from apps.api.app.core.ids import uuid7

router = APIRouter(prefix="/api/v1/admin/research/ziwei")
RULESET_ID = "ziwei-sanhe-research-1.0.0"
DATA_VERSIONS = {
    "tzdb": "2025.2",
    "ephemeris": "astronomy-engine/2.1.19",
    "calendar_dataset": "manual-lunar/1.0.0",
    "ziwei_profiles": "ziwei-profile-registry/1.0.0",
    "ziwei_transformations": "birth-year-transformations-candidate/1.0.0",
    "ziwei_source_claims": "ziwei-source-claim-registry/1.0.0",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LunarBirth(StrictModel):
    year: int = Field(ge=1600, le=2600)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=30)
    is_leap_month: bool
    hour_branch_index: int = Field(ge=0, le=11)
    traditional_sex: str = Field(pattern="^(male|female)$")


class CalendarProvenance(StrictModel):
    conversion_method: str = Field(pattern="^manual_verified_lunar_input$")
    timezone_id: str
    historical_legal_time: str
    user_confirmed: bool
    synthetic: bool = False


class ZiweiPayload(StrictModel):
    profile_record_id: UUID | None = None
    profile_id: str
    profile_version: str
    lunar_birth: LunarBirth
    calendar_provenance: CalendarProvenance
    target_year: int = Field(ge=1600, le=3000)


def _pg():
    from apps.api.app import postgres_app
    return postgres_app


def _owner(token: str | None):
    user = _pg().auth(token)
    if user["role"] != "owner":
        raise HTTPException(403, "owner_only_ziwei_research_preview")
    return user


def _request(payload: dict, run_id: str) -> dict:
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": run_id,
        "run_mode": "research_preview",
        "requested_modules": ["ziwei"],
        "input_snapshot": {
            "operation": "calculate_ziwei_chart",
            "profile_id": payload["profile_id"],
            "profile_version": payload["profile_version"],
            "lunar_birth": payload["lunar_birth"],
            "calendar_provenance": payload["calendar_provenance"],
            "target_year": payload["target_year"],
        },
        "ruleset_bundle_id": RULESET_ID,
        "data_versions": DATA_VERSIONS,
        "deterministic_context": {
            "as_of": "2000-01-01T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
    }


@router.post("/execute", status_code=201)
def execute_ziwei_research(
    payload_model: ZiweiPayload = Body(...),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    module, user = _pg(), _owner(token)
    payload = payload_model.model_dump(mode="json")
    run_id = uuid7()
    try:
        result = execute(_request(payload, str(run_id)))
    except ValueError as exc:
        raise HTTPException(422, exc.as_dict() if hasattr(exc, "as_dict") else "INPUT_INVALID") from exc
    manifest = result["replay_manifest"]
    domain_hash = manifest["domain_result_hashes"]["ziwei_domain_hash"]
    with module.pool.connection() as conn, conn.transaction():
        module.runtime(conn, user)
        claim = module.idempotency(
            conn, user["id"], "POST", "/api/v1/admin/research/ziwei/execute",
            key, module.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        profile_record_id = payload.get("profile_record_id")
        if profile_record_id is not None and not conn.execute(
            "SELECT 1 FROM profiles WHERE id=%s AND owner_id=%s AND deleted_at IS NULL",
            (profile_record_id, user["id"]),
        ).fetchone():
            raise HTTPException(404, "profile_not_found")
        provider = module.provider
        conn.execute(
            """INSERT INTO ziwei_research_runs(
              id,owner_id,profile_record_id,method_profile_id,method_profile_version,
              research_status,review_status,input_snapshot_encrypted,engine_result_encrypted,
              input_hash,output_hash,trace_hash,domain_hash,replay_manifest,
              replay_manifest_hash,ruleset_bundle_id,ruleset_bundle_hash
            ) VALUES(%s,%s,%s,%s,%s,'research_active','UNCONFIRMED',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                run_id, user["id"], profile_record_id, payload["profile_id"],
                payload["profile_version"],
                provider.encrypt(json.dumps(payload, ensure_ascii=False).encode()),
                provider.encrypt(json.dumps(result, ensure_ascii=False).encode()),
                result["input_hash"], result["output_hash"], result["trace_hash"],
                domain_hash, json.dumps(manifest), manifest["content_hash"],
                result["ruleset_bundle_id"], result["ruleset_bundle_hash"],
            ),
        )
        response = {
            "id": str(run_id),
            "mode": "research_preview",
            "banner": "研究预览 · 紫微方法未审校 · 非生产命盘",
            "result": result,
        }
        module.complete(conn, claim, key, 201, response)
        return response


@router.post("/oracle-diff")
def ziwei_oracle_diff(
    payload_model: ZiweiPayload = Body(...),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    _owner(token)
    payload = payload_model.model_dump(mode="json")
    if not payload["calendar_provenance"].get("synthetic"):
        raise HTTPException(422, "oracle_requires_synthetic_or_explicitly_approved_input")
    from oracle_adapters import diff_against_engine, execute_oracle
    engine_result = execute(_request(payload, "synthetic-oracle-diff"))
    lunar = payload["lunar_birth"]
    oracle_result = execute_oracle("ziwei.iztro", {
        "lunar_year": lunar["year"],
        "lunar_month": -lunar["month"] if lunar["is_leap_month"] else lunar["month"],
        "lunar_day": lunar["day"],
        "hour_index": lunar["hour_branch_index"],
        "traditional_sex": lunar["traditional_sex"],
        "profile_id": payload["profile_id"],
    })
    return {
        "mode": "external_differential_evidence",
        "affects_engine_result": False,
        "diff": diff_against_engine(oracle_result, engine_result),
        "oracle": oracle_result,
    }
