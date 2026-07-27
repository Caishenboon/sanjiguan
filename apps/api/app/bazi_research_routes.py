"""Owner-only adapter for the sanji-engine BaZi research contract."""
from __future__ import annotations

import json
from copy import deepcopy
from uuid import UUID

from fastapi import APIRouter, Body, Cookie, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sanji_engine import execute

from apps.api.app.core.ids import uuid7

router = APIRouter(prefix="/api/v1/admin/research/bazi-four-pillars")

RULESET_ID = "bazi-four-pillars-research-1.0.0"
DATA_VERSIONS = {
    "tzdb": "2025.2",
    "ephemeris": "astronomy-engine/2.1.19",
    "calendar_dataset": "calendar-migration-baseline-1.0.0",
    "bazi_method_profiles": "bazi-execution-profiles/1.0.0",
    "bazi_day_epoch": "bazi-day-epoch/1.0.0",
    "bazi_boundary_cases": "bazi-boundary-cases/1.0.0",
    "solar_terms": "astronomy-engine/2.1.19",
}
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BirthPlace(StrictModel):
    latitude: str = Field(pattern=r"^-?[0-9]+(\.[0-9]+)?$")
    longitude: str = Field(pattern=r"^-?[0-9]+(\.[0-9]+)?$")
    name: str
    precision: str


class BirthRecord(StrictModel):
    local_date: str
    local_time: str | None
    calendar_type: str
    time_precision: str
    timezone_id: str
    place: BirthPlace
    user_confirmed: bool


class ProfileRef(StrictModel):
    profile_id: str
    profile_version: str


class BaziExecutePayload(ProfileRef):
    profile_record_id: UUID | None = None
    birth_record: BirthRecord
    input_provenance: dict[str, str] = Field(default_factory=dict)


class BaziComparePayload(StrictModel):
    profiles: list[ProfileRef] = Field(min_length=1, max_length=3)
    birth_record: BirthRecord
    input_provenance: dict[str, str] = Field(default_factory=dict)


def _pg():
    from apps.api.app import postgres_app
    return postgres_app


def _owner(token: str | None):
    user = _pg().auth(token)
    if user["role"] != "owner":
        raise HTTPException(403, "owner_only_bazi_research_preview")
    return user


def _engine_request(payload: dict, run_id: str) -> dict:
    allowed = {
        "profile_record_id", "profile_id", "profile_version",
        "birth_record", "input_provenance",
    }
    unexpected = sorted(set(payload) - allowed)
    if unexpected:
        raise HTTPException(422, {"code": "INPUT_INVALID", "fields": unexpected})
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": run_id,
        "run_mode": "research_preview",
        "requested_modules": ["bazi"],
        "input_snapshot": {
            "operation": "calculate_bazi_four_pillars",
            "profile_id": payload.get("profile_id"),
            "profile_version": payload.get("profile_version"),
            "birth_record": deepcopy(payload.get("birth_record")),
            "input_provenance": deepcopy(payload.get("input_provenance", {})),
        },
        "ruleset_bundle_id": RULESET_ID,
        "data_versions": deepcopy(DATA_VERSIONS),
        "deterministic_context": {
            "as_of": "2000-01-01T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
    }


@router.post("/execute", status_code=201)
def execute_bazi_research(
    payload_model: BaziExecutePayload = Body(...),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    module = _pg()
    user = _owner(token)
    payload = payload_model.model_dump(mode="json")
    run_id = uuid7()
    request = _engine_request(payload, str(run_id))
    try:
        result = execute(request)
    except ValueError as exc:
        detail = exc.as_dict() if hasattr(exc, "as_dict") else {"code": "INPUT_INVALID"}
        raise HTTPException(422, detail) from exc
    manifest = result["replay_manifest"]
    profile_record_id = payload.get("profile_record_id")
    if profile_record_id is not None:
        try:
            profile_record_id = UUID(profile_record_id)
        except (TypeError, ValueError) as exc:
            raise HTTPException(422, "profile_record_id_invalid") from exc
    with module.pool.connection() as conn, conn.transaction():
        module.runtime(conn, user)
        claim = module.idempotency(
            conn, user["id"], "POST",
            "/api/v1/admin/research/bazi-four-pillars/execute",
            key, module.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        if profile_record_id is not None:
            owned = conn.execute(
                "SELECT 1 FROM profiles WHERE id=%s AND owner_id=%s AND deleted_at IS NULL",
                (profile_record_id, user["id"]),
            ).fetchone()
            if not owned:
                raise HTTPException(404, "profile_not_found")
        provider = module.provider
        encrypted_input = provider.encrypt(
            json.dumps(request["input_snapshot"], ensure_ascii=False).encode()
        )
        encrypted_result = provider.encrypt(
            json.dumps(result, ensure_ascii=False).encode()
        )
        conn.execute(
            """INSERT INTO bazi_research_runs(
              id,owner_id,profile_record_id,method_profile_id,method_profile_version,
              research_status,review_status,input_snapshot_encrypted,engine_result_encrypted,
              input_hash,output_hash,trace_hash,replay_manifest,replay_manifest_hash,
              ruleset_bundle_id,ruleset_bundle_hash
            ) VALUES(%s,%s,%s,%s,%s,'research_active','UNCONFIRMED',%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                run_id, user["id"], profile_record_id, payload["profile_id"],
                payload["profile_version"], encrypted_input, encrypted_result,
                result["input_hash"], result["output_hash"], result["trace_hash"],
                json.dumps(manifest), manifest["content_hash"],
                result["ruleset_bundle_id"], result["ruleset_bundle_hash"],
            ),
        )
        response = {
            "id": str(run_id),
            "mode": "research_preview",
            "banner": "研究预览 · 方法未审校 · 非生产命盘",
            "result": result,
        }
        module.complete(conn, claim, key, 201, response)
        return response


@router.post("/compare")
def compare_bazi_profiles(
    payload_model: BaziComparePayload = Body(...),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    _owner(token)
    payload = payload_model.model_dump(mode="json")
    profiles = payload.get("profiles")
    results = []
    for index, profile in enumerate(profiles):
        candidate = {
            "profile_id": profile.get("profile_id"),
            "profile_version": profile.get("profile_version"),
            "birth_record": deepcopy(payload.get("birth_record")),
            "input_provenance": deepcopy(payload.get("input_provenance", {})),
        }
        try:
            engine_result = execute(_engine_request(candidate, f"compare-{index}"))
        except ValueError as exc:
            detail = exc.as_dict() if hasattr(exc, "as_dict") else {"code": "INPUT_INVALID"}
            raise HTTPException(422, detail) from exc
        domain = engine_result["module_results"]["bazi"]["result"]
        results.append({
            "profile_id": profile.get("profile_id"),
            "profile_version": profile.get("profile_version"),
            "candidates": domain["candidates"],
            "domain_hash": engine_result["replay_manifest"]["domain_result_hashes"][
                "bazi_domain_hash"
            ],
        })
    return {
        "mode": "research_preview",
        "banner": "并列研究比较 · 不指定正确主盘",
        "results": results,
        "comparison_domain_hashes": [item["domain_hash"] for item in results],
    }
