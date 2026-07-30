"""Thin private API for the shared deterministic Sprint 17 topic engine."""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Cookie, Header, HTTPException
from sanji_engine import execute, replay

from apps.api.app.core.ids import uuid7
from apps.api.app.liuxiang_archive_routes import (
    DATA_VERSIONS,
    _collect_facts,
    _dec,
    _enc,
    _hash,
    _owned_profile,
    _pg,
    _user,
)

router = APIRouter(prefix="/api/v1")
RULESET_ID = "topic-research-v1.0.0"
TOPICS = {"sushe", "zhongyin_life", "zhongyin_deceased", "yuanqi"}
NOTICE = "三际观原创研究体系 · UNCONFIRMED · 不可生产激活"
NODE_BY_DIMENSION = {
    "lx_ming": "mechanical_chart_reference",
    "lx_ye": "behavior_pattern",
    "lx_yuan": "vow",
    "lx_meng": "dream_tag",
    "lx_yuan_relation": "relationship",
    "lx_shi": "life_event",
}


def _topic_facts(facts: list[dict], excluded: set[str]) -> list[dict]:
    values = []
    for fact in facts:
        if fact["record_id"] in excluded:
            continue
        direction = {
            "positive": "supports",
            "negative": "counters",
        }.get(fact.get("direction"), "neutral")
        tags = sorted(set(
            list(fact.get("confirmed_tags", []))
            + ([fact["state"]] if fact.get("state") else [])
        ))
        consent_scope = (
            "bilateral_analysis"
            if fact.get("relationship_confirmation") == "mutual"
            and fact.get("consent_active")
            else "single_party"
            if fact["dimension_id"] == "lx_yuan_relation"
            else "self"
        )
        values.append({
            "record_id": fact["record_id"],
            "node_type": NODE_BY_DIMENSION[fact["dimension_id"]],
            "occurred_on": fact.get("occurred_on"),
            "date_precision": fact.get("date_precision", "unknown"),
            "tags": tags,
            "direction": direction,
            "magnitude_bp": 0 if fact.get("fact_kind") in {"coverage", "structural"} else 1600,
            "source_reliability_bp": fact.get("source_reliability_bp", 6000),
            "independence_group": fact["record_id"],
            "shared_source_group": fact.get("shared_source_group", fact["record_id"]),
            "consent_scope": consent_scope,
            "withdrawn": fact.get("withdrawn", False),
            "deleted": False,
            "rule_id": "TOPIC.AUTHORIZED.RECORD.V1",
            "rule_version": "1.0.0",
        })
    return values


def _request(
    profile_id: UUID, topic_type: str, facts: list[dict], run_id: UUID,
    as_of: str, relationship_id: str | None,
) -> dict:
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": str(run_id),
        "run_mode": "research_preview",
        "requested_modules": ["signals", "inference"],
        "input_snapshot": {
            "operation": "run_topic_research_v1",
            "topic_type": topic_type,
            "subject_id": str(profile_id),
            "profile_id": str(profile_id),
            "relationship_id": relationship_id,
            "facts": facts,
        },
        "ruleset_bundle_id": RULESET_ID,
        "data_versions": deepcopy(DATA_VERSIONS),
        "deterministic_context": {
            "as_of": as_of,
            "random_method": "none",
            "random_seed": None,
        },
        "requested_trace_level": "full",
    }


def _summary(result: dict) -> list[dict]:
    domain = result["module_results"]["inference"]["result"]
    return [
        {
            "candidate_id": item["candidate_id"],
            "rank": item["rank"],
            "strength_bp": item["strength_bp"],
            "confidence_bp": item["confidence_bp"],
            "status": item["status"],
            "generated_name": (
                item.get("name", {}).get("value")
                if domain["topic_type"] == "sushe" else None
            ),
        }
        for item in domain["candidates"]
    ]


def _stored(conn, execution_id: UUID) -> tuple[dict, dict, dict]:
    row = conn.execute(
        "SELECT * FROM topic_executions WHERE id=%s", (execution_id,)
    ).fetchone()
    if not row:
        raise HTTPException(404, "topic_execution_not_found")
    return row, _dec(row["input_snapshot_encrypted"], {}), _dec(row["result_encrypted"], {})


def _persist(
    conn, user: dict, profile_id: UUID, request: dict, result: dict,
    refs: list[dict], *, kind: str, parent_id: UUID | None, title: str,
) -> tuple[UUID, UUID]:
    execution_id = UUID(request["run_id"])
    domain = result["module_results"]["inference"]["result"]
    graph = result["module_results"]["signals"]["result"]["graph"]
    summary = _summary(result)
    conn.execute(
        """INSERT INTO topic_executions(
          id,owner_id,profile_id,relationship_id,topic_type,parent_execution_id,
          execution_kind,input_snapshot_encrypted,graph_snapshot_encrypted,
          result_encrypted,candidate_summary,engine_version,ruleset_bundle_id,
          topic_ruleset_version,topic_ruleset_hash,naming_ruleset_version,
          naming_ruleset_hash,evidence_policy_version,input_hash,graph_hash,
          output_hash,trace_hash,replay_manifest,status,research_notice
        ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                 %s,%s,%s,%s,%s)""",
        (
            execution_id, user["id"], profile_id,
            request["input_snapshot"].get("relationship_id"),
            domain["topic_type"], parent_id, kind, _enc(request), _enc(graph),
            _enc(result), json.dumps(summary, ensure_ascii=False),
            result["engine_version"], result["ruleset_bundle_id"],
            domain["topic_ruleset_version"], domain["topic_ruleset_hash"],
            domain["naming_ruleset_version"], domain["naming_ruleset_hash"],
            domain["evidence_policy_version"], result["input_hash"],
            graph["graph_hash"], result["output_hash"], result["trace_hash"],
            json.dumps(result["replay_manifest"]), domain["status"], NOTICE,
        ),
    )
    by_id = {item["record_id"]: item for item in request["input_snapshot"]["facts"]}
    for ref in refs:
        fact = by_id.get(ref["record_id"])
        if not fact:
            continue
        conn.execute(
            """INSERT INTO topic_execution_evidence_refs(
              execution_id,owner_id,record_id,record_table,node_type,consent_scope,
              included,withdrawn_at_run,source_fingerprint
            ) VALUES(%s,%s,%s,%s,%s,%s,true,%s,%s)""",
            (
                execution_id, user["id"], UUID(ref["record_id"]), ref["record_table"],
                fact["node_type"], fact["consent_scope"], fact["withdrawn"],
                _hash({"record": ref["record_id"], "revision": ref["record_revision"]}),
            ),
        )
    archive_id = uuid7()
    parent_entry = None
    if parent_id:
        row = conn.execute(
            "SELECT id FROM sanji_archive_entries WHERE topic_execution_id=%s",
            (parent_id,),
        ).fetchone()
        parent_entry = row["id"] if row else None
    conn.execute(
        """INSERT INTO sanji_archive_entries(
          id,owner_id,profile_id,topic_execution_id,parent_entry_id,entry_type,
          title_ciphertext,original_record_refs,status,candidate_summary,engine_version,
          ruleset_version,evidence_policy_version,profile_version,output_hash,trace_hash,
          replay_available,research_notice
        ) VALUES(%s,%s,%s,%s,%s,'topic_research',%s,%s,%s,%s,%s,%s,%s,
                 'profile/current',%s,%s,true,%s)""",
        (
            archive_id, user["id"], profile_id, execution_id, parent_entry, _enc(title),
            json.dumps([
                {"record_id": item["record_id"], "record_table": item["record_table"]}
                for item in refs if item["record_id"] in by_id
            ]),
            domain["status"], json.dumps(summary, ensure_ascii=False),
            result["engine_version"], domain["topic_ruleset_version"],
            domain["evidence_policy_version"], result["output_hash"],
            result["trace_hash"], NOTICE,
        ),
    )
    return execution_id, archive_id


@router.get("/profiles/{profile_id}/topics/{topic_type}/evidence")
def available_evidence(
    profile_id: UUID, topic_type: str,
    token: str | None = Cookie(None, alias="__Host-session"),
):
    if topic_type not in TOPICS:
        raise HTTPException(404, "topic_not_found")
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        facts, refs = _collect_facts(conn, _owned_profile(conn, profile_id, user["id"]))
        values = _topic_facts(facts, set())
    return {
        "topic_type": topic_type,
        "items": values,
        "record_refs": refs,
        "private_text_included": False,
        "research_notice": NOTICE,
    }


@router.post("/profiles/{profile_id}/topics/{topic_type}/executions", status_code=201)
def create_execution(
    profile_id: UUID, topic_type: str, payload: dict = Body(default={}),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    if topic_type not in TOPICS:
        raise HTTPException(404, "topic_not_found")
    excluded = set(payload.get("excluded_record_ids", []))
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/profiles/{id}/topics/{topic}/executions",
            key, pg.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        facts, refs = _collect_facts(
            conn, _owned_profile(conn, profile_id, user["id"])
        )
        topic_facts = _topic_facts(facts, excluded)
        run_id = uuid7()
        request = _request(
            profile_id, topic_type, topic_facts, run_id,
            str(payload.get("as_of") or datetime.now(timezone.utc).isoformat()),
            payload.get("relationship_id"),
        )
        try:
            result = execute(request)
        except ValueError as exc:
            raise HTTPException(
                422, exc.as_dict() if hasattr(exc, "as_dict") else str(exc)
            ) from exc
        execution_id, archive_id = _persist(
            conn, user, profile_id, request, result, refs, kind="initial",
            parent_id=None, title=str(payload.get("title") or f"{topic_type}专题推演"),
        )
        domain = result["module_results"]["inference"]["result"]
        response = {
            "id": str(execution_id), "archive_id": str(archive_id),
            "topic_type": topic_type, "status": domain["status"],
            "strength_bp": domain["strength_bp"],
            "confidence_bp": domain["confidence_bp"],
            "candidates": domain["candidates"],
            "graph_hash": result["module_results"]["signals"]["result"]["graph"]["graph_hash"],
            "output_hash": result["output_hash"], "trace_hash": result["trace_hash"],
            "research_notice": NOTICE,
        }
        pg.complete(conn, claim, key, 201, response)
        return response


@router.get("/topic-executions/{execution_id}")
def get_execution(
    execution_id: UUID,
    token: str | None = Cookie(None, alias="__Host-session"),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        row, _, result = _stored(conn, execution_id)
        return {
            "id": str(row["id"]), "profile_id": str(row["profile_id"]),
            "topic_type": row["topic_type"], "status": row["status"],
            "result": result["module_results"]["inference"]["result"],
            "graph_summary": result["module_results"]["signals"]["result"]["graph"],
            "output_hash": row["output_hash"], "trace_hash": row["trace_hash"],
            "created_at": row["created_at"], "research_notice": NOTICE,
        }


@router.post("/topic-executions/{execution_id}/replay")
def replay_execution(
    execution_id: UUID, key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/topic-executions/{id}/replay",
            key, pg.fingerprint({"execution_id": str(execution_id)}),
        )
        if isinstance(claim, dict):
            return claim
        row, request, original = _stored(conn, execution_id)
        if not row["replay_available"]:
            raise HTTPException(409, {"code": "replay_unavailable"})
        reproduced = replay(row["replay_manifest"], request)
        matched = reproduced["output_hash"] == original["output_hash"]
        conn.execute(
            """INSERT INTO topic_replay_records(
              id,owner_id,execution_id,replay_output_hash,replay_trace_hash,matched
            ) VALUES(%s,%s,%s,%s,%s,%s)""",
            (uuid7(), user["id"], execution_id, reproduced["output_hash"],
             reproduced["trace_hash"], matched),
        )
        response = {
            "execution_id": str(execution_id), "matched": matched,
            "output_hash": reproduced["output_hash"],
            "trace_hash": reproduced["trace_hash"],
        }
        pg.complete(conn, claim, key, 200, response)
        return response


@router.delete("/topic-executions/{execution_id}/input-snapshot", status_code=202)
def purge_execution_input_snapshot(
    execution_id: UUID, key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    """Irreversibly erase normalized private input and graph snapshots."""
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "DELETE",
            "/api/v1/topic-executions/{id}/input-snapshot",
            key, pg.fingerprint({"execution_id": str(execution_id)}),
        )
        if isinstance(claim, dict):
            return claim
        row, _, _ = _stored(conn, execution_id)
        if row["replay_available"]:
            conn.execute(
                """UPDATE topic_executions
                   SET input_snapshot_encrypted=NULL,graph_snapshot_encrypted=NULL,
                       replay_available=false,
                       replay_unavailable_reason='input_snapshot_erased_by_user',
                       snapshot_purged_at=now()
                   WHERE id=%s""",
                (execution_id,),
            )
            conn.execute(
                """UPDATE sanji_archive_entries SET replay_available=false
                   WHERE topic_execution_id=%s""",
                (execution_id,),
            )
        response = {
            "execution_id": str(execution_id), "snapshot_erased": True,
            "graph_erased": True, "replay_available": False,
            "replay_status": "replay_unavailable",
        }
        pg.complete(conn, claim, key, 202, response)
        return response


@router.post("/topic-executions/{execution_id}/reanalyze", status_code=201)
def reanalyze_execution(
    execution_id: UUID, payload: dict = Body(default={}),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/topic-executions/{id}/reanalyze",
            key, pg.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        parent, _, _ = _stored(conn, execution_id)
        facts, refs = _collect_facts(
            conn, _owned_profile(conn, parent["profile_id"], user["id"])
        )
        request = _request(
            parent["profile_id"], parent["topic_type"],
            _topic_facts(facts, set(payload.get("excluded_record_ids", []))),
            uuid7(), str(payload.get("as_of") or datetime.now(timezone.utc).isoformat()),
            str(parent["relationship_id"]) if parent["relationship_id"] else None,
        )
        result = execute(request)
        new_id, archive_id = _persist(
            conn, user, parent["profile_id"], request, result, refs,
            kind="reanalysis", parent_id=execution_id,
            title=str(payload.get("title") or f"{parent['topic_type']}重新分析"),
        )
        response = {
            "id": str(new_id), "archive_id": str(archive_id),
            "parent_execution_id": str(execution_id), "creates_new_record": True,
        }
        pg.complete(conn, claim, key, 201, response)
        return response


def _comparison(left: dict, right: dict, left_request: dict, right_request: dict) -> dict:
    left_ids = {item["record_id"] for item in left_request["input_snapshot"]["facts"]}
    right_ids = {item["record_id"] for item in right_request["input_snapshot"]["facts"]}
    return {
        "input_records_added": sorted(right_ids - left_ids),
        "input_records_removed_or_withdrawn": sorted(left_ids - right_ids),
        "engine_changed": left["engine_version"] != right["engine_version"],
        "topic_ruleset_changed": left["topic_ruleset_hash"] != right["topic_ruleset_hash"],
        "naming_ruleset_changed": left["naming_ruleset_hash"] != right["naming_ruleset_hash"],
        "naming_change_reason": (
            "姓名规则版本变化"
            if left["naming_ruleset_hash"] != right["naming_ruleset_hash"] else None
        ),
        "topic_changed": left["topic_type"] != right["topic_type"],
        "candidate_order_changed": left["candidate_summary"] != right["candidate_summary"],
        "output_changed": left["output_hash"] != right["output_hash"],
    }


@router.post("/topic-executions/compare")
def compare_executions(
    payload: dict = Body(...), key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    try:
        left_id = UUID(payload["left_execution_id"])
        right_id = UUID(payload["right_execution_id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(422, "two_execution_ids_required") from exc
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/topic-executions/compare",
            key, pg.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        left, left_request, _ = _stored(conn, left_id)
        right, right_request, _ = _stored(conn, right_id)
        if left["profile_id"] != right["profile_id"]:
            raise HTTPException(409, "executions_must_share_profile")
        if not left["replay_available"] or not right["replay_available"]:
            raise HTTPException(409, {"code": "replay_unavailable"})
        summary = _comparison(left, right, left_request, right_request)
        comparison_id, comparison_hash = uuid7(), _hash(summary)
        conn.execute(
            """INSERT INTO topic_execution_comparisons(
              id,owner_id,left_execution_id,right_execution_id,difference_summary,comparison_hash
            ) VALUES(%s,%s,%s,%s,%s,%s)""",
            (comparison_id, user["id"], left_id, right_id,
             json.dumps(summary, ensure_ascii=False), comparison_hash),
        )
        response = {
            "id": str(comparison_id), "differences": summary,
            "comparison_hash": comparison_hash,
        }
        pg.complete(conn, claim, key, 200, response)
        return response
