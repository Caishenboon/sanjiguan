"""Thin private API for deterministic life-trend and controlled prose."""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Cookie, Header, HTTPException
from sanji_engine import execute, replay

from apps.api.app.core.runtime import SESSION_COOKIE_NAME

from apps.api.app.core.ids import uuid7
from apps.api.app.liuxiang_archive_routes import (
    DATA_VERSIONS, _collect_facts, _dec, _enc, _hash, _owned_profile, _pg, _user,
)
from packages.research_inference.life_trend_narrative import (
    build_narrative_payload,
    controlled_narrative_or_fallback,
)
from packages.research_inference.providers import DeepSeekProvider

router = APIRouter(prefix="/api/v1")
RULESET_ID = "life-trend-research-v1.0.0"
NOTICE = "三际观原创研究体系 · UNCONFIRMED · 不可生产激活"


def _factor(fact: dict) -> dict:
    kind = fact.get("fact_kind", "evidence")
    direction = {"positive": "supports", "negative": "counters"}.get(
        fact.get("direction"), "neutral"
    )
    scoring = kind not in {"coverage", "structural"} and not fact.get("withdrawn", False)
    return {
        "factor_id": f"{fact['record_id']}:{fact['dimension_id']}",
        "factor_type": fact["dimension_id"],
        "factor_kind": kind if kind in {"coverage", "structural"} else "evidence",
        "source_system": "authorized_user_record",
        "source_record_id": fact["record_id"],
        "source_fact_path": f"record/{fact['dimension_id']}",
        "occurred_on": fact.get("occurred_on"),
        "date_precision": fact.get("date_precision", "unknown"),
        "direction": direction if scoring else "neutral",
        "magnitude_bp": 1600 if scoring else 0,
        "source_reliability_bp": fact.get("source_reliability_bp", 6000),
        "mapping_reliability_bp": 7000,
        "independence_group": fact["record_id"],
        "shared_source_group": fact.get("shared_source_group") or fact["record_id"],
        "tags": sorted(set(fact.get("confirmed_tags", []))),
        "boundary_sensitivity_bp": fact.get("boundary_sensitivity_bp", 0),
        "conflict": bool(fact.get("conflicts")),
        "epistemic_status": "observed",
        "rule_id": "LIFE_TREND.AUTHORIZED_RECORD.V1",
        "rule_version": "1.0.0",
    }


def _request(profile_id: UUID, factors: list[dict], run_id: UUID, payload: dict) -> dict:
    as_of = str(payload.get("as_of") or datetime.now(timezone.utc).isoformat())
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": str(run_id),
        "run_mode": "research_preview",
        "requested_modules": ["life-chart"],
        "input_snapshot": {
            "operation": "run_life_trend_v1",
            "profile_id": str(profile_id),
            "subject_id": str(profile_id),
            "as_of": as_of,
            "start_date": payload.get("start_date"),
            "end_date": payload.get("end_date"),
            "granularity": payload.get("granularity", "auto"),
            "future_bucket_count": int(payload.get("future_bucket_count", 2)),
            "factors": factors,
        },
        "ruleset_bundle_id": RULESET_ID,
        "data_versions": deepcopy(DATA_VERSIONS),
        "deterministic_context": {
            "as_of": as_of, "random_method": "none", "random_seed": None,
        },
        "requested_trace_level": "full",
    }


def _domain(result: dict) -> dict:
    return result["module_results"]["life-chart"]["result"]


def _overall_status(domain: dict) -> str:
    effective = [item for item in domain["buckets"] if item["candle"] is not None]
    return effective[-1]["status"] if effective else "insufficient"


def _stored(conn, execution_id: UUID) -> tuple[dict, dict, dict]:
    row = conn.execute(
        "SELECT * FROM life_trend_executions WHERE id=%s", (execution_id,)
    ).fetchone()
    if not row:
        raise HTTPException(404, "life_trend_execution_not_found")
    return (
        row,
        _dec(row["input_snapshot_encrypted"], {}),
        _dec(row["core_result_encrypted"], {}),
    )


def _persist(
    conn, user: dict, profile_id: UUID, request: dict, result: dict, *,
    kind: str, parent_id: UUID | None, title: str,
) -> tuple[UUID, UUID]:
    execution_id = UUID(request["run_id"])
    domain = _domain(result)
    status = _overall_status(domain)
    conn.execute(
        """INSERT INTO life_trend_executions(
          id,owner_id,profile_id,parent_execution_id,execution_kind,
          input_snapshot_encrypted,core_result_encrypted,deterministic_report_encrypted,
          engine_version,ruleset_bundle_id,life_trend_ruleset_version,
          evidence_policy_version,report_template_version,input_hash,core_output_hash,
          deterministic_report_hash,narrative_input_hash,output_hash,trace_hash,
          replay_manifest,status,research_notice
        ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            execution_id, user["id"], profile_id, parent_id, kind, _enc(request),
            _enc(result), _enc(domain["deterministic_report"]), result["engine_version"],
            RULESET_ID, domain["ruleset_version"], domain["evidence_policy_version"],
            domain["report_template_version"], result["input_hash"],
            domain["core_output_hash"], domain["deterministic_report_hash"],
            domain["narrative_input_hash"], result["output_hash"], domain["trace_hash"],
            json.dumps(result["replay_manifest"]), status, NOTICE,
        ),
    )
    for sequence, bucket in enumerate(domain["buckets"]):
        conn.execute(
            """INSERT INTO life_trend_buckets(
              execution_id,owner_id,bucket_id,sequence_no,starts_on,ends_on,
              time_precision,segment,candle,confidence_bp,coverage_bp,trace_ref
            ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                execution_id, user["id"], bucket["bucket_id"], sequence,
                bucket["start"], bucket["end"], bucket["time_precision"],
                bucket["segment"],
                json.dumps(bucket["candle"]) if bucket["candle"] else None,
                bucket["confidence_bp"], bucket["coverage_bp"], bucket["trace_ref"],
            ),
        )
    for window in domain["timing_windows"]:
        conn.execute(
            """INSERT INTO life_trend_timing_windows(
              execution_id,owner_id,window_id,starts_on,ends_on,precision,window_type,
              strength_bp,confidence_bp,status,payload
            ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                execution_id, user["id"], window["window_id"], window["start"],
                window["end"], window["time_precision"], window["type"],
                window["strength_bp"], window["confidence_bp"], window["status"],
                json.dumps(window, ensure_ascii=False),
            ),
        )
    archive_id = uuid7()
    effective = [item for item in domain["buckets"] if item["candle"] is not None]
    latest = effective[-1] if effective else None
    parent_entry = None
    if parent_id:
        parent = conn.execute(
            "SELECT id FROM sanji_archive_entries WHERE life_trend_execution_id=%s",
            (parent_id,),
        ).fetchone()
        parent_entry = parent["id"] if parent else None
    conn.execute(
        """INSERT INTO sanji_archive_entries(
          id,owner_id,profile_id,life_trend_execution_id,parent_entry_id,entry_type,
          title_ciphertext,original_record_refs,status,candidate_summary,engine_version,
          ruleset_version,evidence_policy_version,profile_version,output_hash,trace_hash,
          replay_available,research_notice
        ) VALUES(%s,%s,%s,%s,%s,'life_trend_report',%s,'[]'::jsonb,%s,%s,%s,%s,%s,
                 'profile/current',%s,%s,true,%s)""",
        (
            archive_id, user["id"], profile_id, execution_id, parent_entry, _enc(title),
            status, json.dumps([{
                "candidate_id": "life-trend",
                "strength_bp": abs(latest["candle"]["close"]) if latest else 0,
                "confidence_bp": latest["confidence_bp"] if latest else 0,
                "status": status,
                "auspice": domain["deterministic_report"]["auspice"],
            }], ensure_ascii=False),
            result["engine_version"], domain["ruleset_version"],
            domain["evidence_policy_version"], result["output_hash"],
            domain["trace_hash"], NOTICE,
        ),
    )
    return execution_id, archive_id


@router.get("/profiles/{profile_id}/life-trend/evidence")
def available_evidence(
    profile_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        facts, _ = _collect_facts(conn, _owned_profile(conn, profile_id, user["id"]))
    return {
        "profile_id": str(profile_id), "factors": [_factor(item) for item in facts],
        "full_private_text_included": False, "research_notice": NOTICE,
    }


@router.post("/profiles/{profile_id}/life-trend/executions", status_code=201)
def create_execution(
    profile_id: UUID, payload: dict = Body(default={}),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/profiles/{id}/life-trend/executions",
            key, pg.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        facts, _ = _collect_facts(conn, _owned_profile(conn, profile_id, user["id"]))
        excluded = set(payload.get("excluded_record_ids", []))
        factors = [_factor(item) for item in facts if item["record_id"] not in excluded]
        request = _request(profile_id, factors, uuid7(), payload)
        result = execute(request)
        execution_id, archive_id = _persist(
            conn, user, profile_id, request, result, kind="initial", parent_id=None,
            title=str(payload.get("title") or "命势长图与三际断章"),
        )
        domain = _domain(result)
        response = {
            "id": str(execution_id), "archive_id": str(archive_id),
            "status": _overall_status(domain), "timeline": domain["buckets"],
            "timing_windows": domain["timing_windows"],
            "report": domain["deterministic_report"],
            "core_output_hash": domain["core_output_hash"],
            "deterministic_report_hash": domain["deterministic_report_hash"],
            "trace_hash": domain["trace_hash"], "research_notice": NOTICE,
        }
        pg.complete(conn, claim, key, 201, response)
        return response


@router.get("/life-trend-executions/{execution_id}")
def get_execution(
    execution_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        row, _, result = _stored(conn, execution_id)
        domain = _domain(result)
        return {
            "id": str(row["id"]), "profile_id": str(row["profile_id"]),
            "status": row["status"], "timeline": domain["buckets"],
            "timing_windows": domain["timing_windows"],
            "report": domain["deterministic_report"],
            "ai_narrative": _dec(row["ai_narrative_encrypted"], None),
            "ai_status": row["ai_status"], "core_output_hash": row["core_output_hash"],
            "deterministic_report_hash": row["deterministic_report_hash"],
            "narrative_input_hash": row["narrative_input_hash"],
            "narrative_output_hash": row["narrative_output_hash"],
            "trace_hash": row["trace_hash"], "research_notice": NOTICE,
        }


@router.get("/life-trend-executions/{execution_id}/buckets/{bucket_id}")
def get_bucket(
    execution_id: UUID, bucket_id: str,
    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        _, _, result = _stored(conn, execution_id)
        bucket = next(
            (item for item in _domain(result)["buckets"] if item["bucket_id"] == bucket_id),
            None,
        )
        if not bucket:
            raise HTTPException(404, "life_trend_bucket_not_found")
        return bucket


@router.post("/life-trend-executions/{execution_id}/narrative")
def create_narrative(
    execution_id: UUID, payload: dict = Body(default={}),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/life-trend-executions/{id}/narrative",
            key, pg.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        _, _, result = _stored(conn, execution_id)
        domain = _domain(result)
        provider_output = None
        provider_error = None
        metrics = {}
        if payload.get("external_model_confirmed"):
            try:
                provider = DeepSeekProvider()
                generated = provider.generate_life_trend_with_metrics(
                    build_narrative_payload(domain)
                )
                provider_output = generated["content"]
                metrics = {
                    "provider": provider.name,
                    "model": generated.get("model"),
                    "usage": generated.get("usage", {}),
                }
            except (RuntimeError, ValueError) as exc:
                provider_error = exc
        else:
            provider_error = RuntimeError("external_model_not_confirmed")
        narrative = controlled_narrative_or_fallback(domain, provider_output, provider_error)
        ai_status = "accepted" if narrative["status"] == "accepted" else "fallback"
        conn.execute(
            """UPDATE life_trend_executions
               SET ai_narrative_encrypted=%s,narrative_output_hash=%s,ai_status=%s,
                   ai_provider=%s,ai_model=%s,prompt_version='life-trend-report-1.0.0',
                   ai_generated_at=now()
               WHERE id=%s""",
            (
                _enc(narrative), narrative["narrative_output_hash"], ai_status,
                metrics.get("provider"), metrics.get("model"), execution_id,
            ),
        )
        response = {
            "execution_id": str(execution_id), **narrative,
            "provider": metrics.get("provider"), "model": metrics.get("model"),
        }
        pg.complete(conn, claim, key, 200, response)
        return response


@router.post("/life-trend-executions/{execution_id}/replay")
def replay_execution(
    execution_id: UUID, key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/life-trend-executions/{id}/replay",
            key, pg.fingerprint({"execution_id": str(execution_id)}),
        )
        if isinstance(claim, dict):
            return claim
        row, request, original = _stored(conn, execution_id)
        if not row["replay_available"]:
            raise HTTPException(409, {"code": "replay_unavailable"})
        reproduced = replay(row["replay_manifest"], request)
        new_domain, old_domain = _domain(reproduced), _domain(original)
        matched = (
            new_domain["core_output_hash"] == old_domain["core_output_hash"]
            and new_domain["trace_hash"] == old_domain["trace_hash"]
        )
        conn.execute(
            """INSERT INTO life_trend_replay_records(
              id,owner_id,execution_id,replay_core_output_hash,replay_trace_hash,matched
            ) VALUES(%s,%s,%s,%s,%s,%s)""",
            (
                uuid7(), user["id"], execution_id, new_domain["core_output_hash"],
                new_domain["trace_hash"], matched,
            ),
        )
        response = {
            "execution_id": str(execution_id), "matched": matched,
            "core_output_hash": new_domain["core_output_hash"],
            "trace_hash": new_domain["trace_hash"],
        }
        pg.complete(conn, claim, key, 200, response)
        return response


@router.delete("/life-trend-executions/{execution_id}/input-snapshot", status_code=202)
def purge_input_snapshot(
    execution_id: UUID, key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME),
):
    """Irreversibly erase normalized private input; Replay then fails explicitly."""
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "DELETE",
            "/api/v1/life-trend-executions/{id}/input-snapshot",
            key, pg.fingerprint({"execution_id": str(execution_id)}),
        )
        if isinstance(claim, dict):
            return claim
        row, _, _ = _stored(conn, execution_id)
        if row["replay_available"]:
            conn.execute(
                """UPDATE life_trend_executions
                   SET input_snapshot_encrypted=NULL,replay_available=false,
                       replay_unavailable_reason='input_snapshot_erased_by_user',
                       snapshot_purged_at=now()
                   WHERE id=%s""",
                (execution_id,),
            )
            conn.execute(
                """UPDATE sanji_archive_entries SET replay_available=false
                   WHERE life_trend_execution_id=%s""", (execution_id,),
            )
        response = {
            "execution_id": str(execution_id), "snapshot_erased": True,
            "replay_available": False, "replay_status": "replay_unavailable",
        }
        pg.complete(conn, claim, key, 202, response)
        return response


@router.post("/life-trend-executions/{execution_id}/reanalyze", status_code=201)
def reanalyze(
    execution_id: UUID, payload: dict = Body(default={}),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/life-trend-executions/{id}/reanalyze",
            key, pg.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        parent, _, _ = _stored(conn, execution_id)
        facts, _ = _collect_facts(
            conn, _owned_profile(conn, parent["profile_id"], user["id"])
        )
        excluded = set(payload.get("excluded_record_ids", []))
        request = _request(
            parent["profile_id"], [_factor(x) for x in facts if x["record_id"] not in excluded],
            uuid7(), payload,
        )
        result = execute(request)
        new_id, archive_id = _persist(
            conn, user, parent["profile_id"], request, result, kind="reanalysis",
            parent_id=execution_id, title=str(payload.get("title") or "命势长图重新分析"),
        )
        response = {
            "id": str(new_id), "archive_id": str(archive_id),
            "parent_execution_id": str(execution_id), "creates_new_record": True,
        }
        pg.complete(conn, claim, key, 201, response)
        return response


@router.post("/life-trend-executions/compare")
def compare(
    payload: dict = Body(...), key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME),
):
    try:
        left_id, right_id = UUID(payload["left_execution_id"]), UUID(payload["right_execution_id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(422, "two_execution_ids_required") from exc
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/life-trend-executions/compare",
            key, pg.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        left, left_request, left_result = _stored(conn, left_id)
        right, right_request, right_result = _stored(conn, right_id)
        if left["profile_id"] != right["profile_id"]:
            raise HTTPException(409, "executions_must_share_profile")
        left_factors = {
            item["factor_id"] for item in left_request["input_snapshot"]["factors"]
        }
        right_factors = {
            item["factor_id"] for item in right_request["input_snapshot"]["factors"]
        }
        left_domain, right_domain = _domain(left_result), _domain(right_result)
        differences = {
            "input_factors_added": sorted(right_factors - left_factors),
            "input_factors_removed_or_withdrawn": sorted(left_factors - right_factors),
            "engine_changed": left["engine_version"] != right["engine_version"],
            "ruleset_changed": left["life_trend_ruleset_version"] != right["life_trend_ruleset_version"],
            "policy_changed": left["evidence_policy_version"] != right["evidence_policy_version"],
            "granularity_changed": left_domain["granularity"] != right_domain["granularity"],
            "data_precision_changed": sorted({
                item["factor_id"] for item in left_domain["factors"]
                if next((r for r in right_domain["factors"] if r["factor_id"] == item["factor_id"]
                         and r["date_precision"] != item["date_precision"]), None)
            }),
            "core_output_changed": left["core_output_hash"] != right["core_output_hash"],
        }
        comparison_id, comparison_hash = uuid7(), _hash(differences)
        conn.execute(
            """INSERT INTO life_trend_execution_comparisons(
              id,owner_id,left_execution_id,right_execution_id,difference_summary,comparison_hash
            ) VALUES(%s,%s,%s,%s,%s,%s)""",
            (
                comparison_id, user["id"], left_id, right_id,
                json.dumps(differences, ensure_ascii=False), comparison_hash,
            ),
        )
        response = {
            "id": str(comparison_id), "differences": differences,
            "comparison_hash": comparison_hash,
        }
        pg.complete(conn, claim, key, 200, response)
        return response
