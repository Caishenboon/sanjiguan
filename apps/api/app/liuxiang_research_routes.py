"""Thin owner-only API for deterministic Liuxiang research v1."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Body, Cookie, Header, HTTPException
from sanji_engine import execute, replay

from apps.api.app.core.ids import uuid7
from packages.research_data.core import load_manifests

router = APIRouter(prefix="/api/v1/admin/research/liuxiang")
ROOT = Path(__file__).resolve().parents[3]
RULESET_ID = "liuxiang-research-v1.0.0"
DATA_VERSIONS = {
    "tzdb": "2025.2",
    "ephemeris": "astronomy-engine/2.1.19",
    "calendar_dataset": "calendar-baseline/1.0.0",
}
ASSET_CLASSES = {
    "synthetic_conformance", "mechanical_reference", "external_research_unverified",
    "retrospective_observational", "prospective_blind",
}


def _pg():
    from apps.api.app import postgres_app
    return postgres_app


def _owner(token: str | None):
    user = _pg().auth(token)
    if user["role"] != "owner":
        raise HTTPException(403, "owner_only_liuxiang_research")
    return user


def _request(payload: dict, run_id: str) -> dict:
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": run_id,
        "run_mode": "research_preview",
        "requested_modules": ["signals", "inference"],
        "input_snapshot": {
            "operation": "run_liuxiang_research_v1",
            "subject_id": payload.get("subject_id", f"research:{run_id}"),
            "signals": deepcopy(payload.get("signals", [])),
            "completeness_bp_by_dimension": deepcopy(
                payload.get("completeness_bp_by_dimension", {})
            ),
        },
        "ruleset_bundle_id": RULESET_ID,
        "data_versions": deepcopy(DATA_VERSIONS),
        "deterministic_context": {
            "as_of": payload.get("as_of", "2026-07-28T00:00:00Z"),
            "random_method": "none",
            "random_seed": None,
        },
        "requested_trace_level": "full",
    }


@router.get("/sources")
def list_sources(token: str | None = Cookie(None, alias="__Host-session")):
    _owner(token)
    return {"items": [{
        "dataset_id": value["dataset_id"],
        "revision": value["pinned_revision"],
        "license_review_status": value["license_review_status"],
        "connector_enabled": value["connector_enabled"],
        "shared_source_group": value["shared_source_group"],
    } for value in load_manifests()]}


@router.get("/quality")
def quality(token: str | None = Cookie(None, alias="__Host-session")):
    _owner(token)
    return json.loads(
        (ROOT / "research-data/reports/vedastro-quality-2026-07-28.json").read_text(
            encoding="utf-8"
        )
    )


@router.get("/matching")
def matching(token: str | None = Cookie(None, alias="__Host-session")):
    return quality(token)["matching"]


@router.get("/aggregate-report")
def aggregate_report(token: str | None = Cookie(None, alias="__Host-session")):
    _owner(token)
    return {
        "quality": quality(token),
        "baseline": json.loads(
            (ROOT / "research-data/reports/permutation-baseline-synthetic.json").read_text(
                encoding="utf-8"
            )
        ),
        "notice": "研究覆盖与合成协议结果不能证明现实预测能力或因果关系。",
    }


@router.post("/executions", status_code=201)
def create_execution(
    payload: dict = Body(...),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    module, user = _pg(), _owner(token)
    asset_class = payload.get("asset_class")
    if asset_class not in ASSET_CLASSES:
        raise HTTPException(422, "invalid_research_asset_class")
    if asset_class == "prospective_blind":
        raise HTTPException(409, "prospective_blind_entry_disabled")
    run_id = uuid7()
    request = _request(payload, str(run_id))
    try:
        result = execute(request)
    except ValueError as exc:
        detail = exc.as_dict() if hasattr(exc, "as_dict") else {"code": "INPUT_INVALID"}
        raise HTTPException(422, detail) from exc
    profile_record_id = payload.get("profile_record_id")
    with module.pool.connection() as conn, conn.transaction():
        module.runtime(conn, user)
        claim = module.idempotency(
            conn, user["id"], "POST", "/api/v1/admin/research/liuxiang/executions",
            key, module.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        if profile_record_id:
            owned = conn.execute(
                "SELECT 1 FROM profiles WHERE id=%s AND owner_id=%s AND deleted_at IS NULL",
                (profile_record_id, user["id"]),
            ).fetchone()
            if not owned:
                raise HTTPException(404, "profile_not_found")
        provider = module.provider
        manifest = result["replay_manifest"]
        conn.execute(
            """INSERT INTO liuxiang_research_executions(
              id,owner_id,profile_record_id,asset_class,research_status,review_status,
              production_activatable,input_snapshot_encrypted,engine_result_encrypted,
              input_hash,output_hash,trace_hash,replay_manifest,replay_manifest_hash,
              ruleset_bundle_id,ruleset_bundle_hash
            ) VALUES(%s,%s,%s,%s,'research_active','UNCONFIRMED',false,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                run_id, user["id"], profile_record_id, asset_class,
                provider.encrypt(json.dumps(request, ensure_ascii=False).encode()),
                provider.encrypt(json.dumps(result, ensure_ascii=False).encode()),
                result["input_hash"], result["output_hash"], result["trace_hash"],
                json.dumps(manifest), manifest["content_hash"],
                result["ruleset_bundle_id"], result["ruleset_bundle_hash"],
            ),
        )
        domain = result["module_results"]["inference"]["result"]
        signals = result["module_results"]["signals"]["result"]["signals"]
        for signal in signals:
            conn.execute(
                """INSERT INTO liuxiang_research_signals(
                  id,owner_id,execution_id,signal_id,dimension_id,independence_group,
                  shared_source_group,signal_json,content_hash
                ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    uuid7(), user["id"], run_id, signal["signal_id"],
                    signal["dimension_id"], signal["independence_group"],
                    signal["shared_source_group"], json.dumps(signal), signal["content_hash"],
                ),
            )
        for candidate in domain["candidates"]:
            conn.execute(
                """INSERT INTO liuxiang_research_candidates(
                  id,owner_id,execution_id,candidate_id,dimension_id,strength_bp,
                  confidence_bp,status,rank,candidate_json,result_hash
                ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    uuid7(), user["id"], run_id, candidate["candidate_id"],
                    candidate["dimension_id"], candidate["calibrated_strength_bp"],
                    candidate["confidence_bp"], candidate["status"], candidate["rank"],
                    json.dumps(candidate), candidate["result_hash"],
                ),
            )
        response = {
            "id": str(run_id),
            "status": domain["status"],
            "strength_bp": domain["strength_bp"],
            "confidence_bp": domain["confidence_bp"],
            "output_hash": result["output_hash"],
            "banner": "三际观原创研究体系 · UNCONFIRMED · 不可生产激活",
        }
        module.complete(conn, claim, key, 201, response)
        return response


def _stored(execution_id: UUID, token: str | None) -> tuple[dict, dict, dict]:
    module, user = _pg(), _owner(token)
    with module.pool.connection() as conn, conn.transaction():
        module.runtime(conn, user)
        row = conn.execute(
            """SELECT id,input_snapshot_encrypted,engine_result_encrypted,replay_manifest
               FROM liuxiang_research_executions
               WHERE id=%s AND deleted_at IS NULL""",
            (execution_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "liuxiang_execution_not_found")
        request = json.loads(module.provider.decrypt(row["input_snapshot_encrypted"]).decode())
        result = json.loads(module.provider.decrypt(row["engine_result_encrypted"]).decode())
        return request, result, row["replay_manifest"]


@router.get("/executions/{execution_id}")
def get_execution(
    execution_id: UUID,
    token: str | None = Cookie(None, alias="__Host-session"),
):
    _, result, _ = _stored(execution_id, token)
    return {
        "id": str(execution_id),
        "result": result["module_results"]["inference"]["result"],
        "output_hash": result["output_hash"],
    }


@router.get("/executions/{execution_id}/candidates")
def get_candidates(execution_id: UUID, token: str | None = Cookie(None, alias="__Host-session")):
    return {"items": get_execution(execution_id, token)["result"]["candidates"]}


@router.get("/executions/{execution_id}/evidence")
def get_evidence(execution_id: UUID, token: str | None = Cookie(None, alias="__Host-session")):
    _, result, _ = _stored(execution_id, token)
    return result["module_results"]["signals"]["result"]


@router.get("/executions/{execution_id}/trace")
def get_trace(execution_id: UUID, token: str | None = Cookie(None, alias="__Host-session")):
    _, result, _ = _stored(execution_id, token)
    return {"trace": result["trace"], "trace_hash": result["trace_hash"]}


@router.post("/executions/{execution_id}/replay")
def replay_execution(
    execution_id: UUID,
    token: str | None = Cookie(None, alias="__Host-session"),
):
    request, original, manifest = _stored(execution_id, token)
    reproduced = replay(manifest, request)
    return {
        "output_hash": reproduced["output_hash"],
        "matches_original": reproduced["output_hash"] == original["output_hash"],
    }


@router.post("/compare")
def compare_research(
    payload: dict = Body(...),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    _owner(token)
    variants = payload.get("variants")
    if not isinstance(variants, list) or not 1 <= len(variants) <= 4:
        raise HTTPException(422, "one_to_four_variants_required")
    results = []
    for index, variant in enumerate(variants):
        result = execute(_request(variant, f"liuxiang-compare-{index}"))
        domain = result["module_results"]["inference"]["result"]
        results.append({
            "label": variant.get("label", f"variant-{index + 1}"),
            "status": domain["status"],
            "strength_bp": domain["strength_bp"],
            "confidence_bp": domain["confidence_bp"],
            "result_hash": domain["result_hash"],
        })
    return {"items": results, "ruleset_id": RULESET_ID}
