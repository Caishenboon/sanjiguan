"""Private Liuxiang evidence execution and authoritative Sanji archive API."""
from __future__ import annotations

import json
import hashlib
from copy import deepcopy
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Cookie, Header, HTTPException
from sanji_engine import execute, replay

from apps.api.app.core.ids import uuid7

router = APIRouter(prefix="/api/v1")
RULESET_ID = "liuxiang-evidence-research-v1.0.0"
NOTICE = "三际观原创研究体系 · UNCONFIRMED · 不可生产激活"
DATA_VERSIONS = {
    "tzdb": "2025.2",
    "ephemeris": "astronomy-engine/2.1.19",
    "calendar_dataset": "calendar-baseline/1.0.0",
}


def _hash(value: object) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"
DOMAIN_DIMENSIONS = {
    "ming": "lx_ming",
    "karma": "lx_ye",
    "vow": "lx_yuan",
    "dream": "lx_meng",
    "relation": "lx_yuan_relation",
    "life_event": "lx_shi",
}
JOURNAL_DIMENSIONS = {
    "practice": "lx_ye",
    "affliction": "lx_ye",
    "vow_action": "lx_yuan",
    "dream": "lx_meng",
    "relationship": "lx_yuan_relation",
    "life_event": "lx_shi",
}


def _pg():
    from apps.api.app import postgres_app
    return postgres_app


def _user(token):
    return _pg().auth(token)


def _enc(value: object) -> bytes:
    return _pg().provider.encrypt(
        json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")
    )


def _dec(value: bytes | None, default=None):
    if value is None:
        return default
    return json.loads(_pg().provider.decrypt(value).decode("utf-8"))


def _owned_profile(conn, profile_id: UUID, owner_id: UUID) -> dict:
    row = conn.execute(
        """SELECT * FROM profiles
           WHERE id=%s AND owner_id=%s AND deleted_at IS NULL""",
        (profile_id, owner_id),
    ).fetchone()
    if not row:
        raise HTTPException(404, "profile_not_found")
    return row


def _date_value(value: object) -> tuple[str | None, str]:
    if value is None:
        return None, "unknown"
    if isinstance(value, datetime):
        return value.date().isoformat(), "exact_date"
    if isinstance(value, date):
        return value.isoformat(), "exact_date"
    text = str(value)
    if len(text) == 4 and text.isdigit():
        return text, "year_only"
    if len(text) == 7:
        return text, "month_only"
    try:
        return date.fromisoformat(text[:10]).isoformat(), "exact_date"
    except ValueError:
        return None, "unknown"


def _record_fact(
    *,
    record_id: object,
    dimension_id: str,
    occurred_on: object,
    state: str,
    direction: str = "positive",
    tags: list[str] | None = None,
    reliability_bp: int = 7000,
    shared_source_group: str | None = None,
    withdrawn: bool = False,
    source_type: str = "user_record",
    verification_status: str = "user_self_report",
    relationship_confirmation: str = "not_applicable",
    consent_active: bool = True,
    conflicts: list[str] | None = None,
) -> dict:
    occurred, precision = _date_value(occurred_on)
    return {
        "record_id": str(record_id),
        "dimension_id": dimension_id,
        "fact_kind": "evidence",
        "occurred_on": occurred,
        "date_precision": precision,
        "state": state,
        "direction": direction if direction in {"positive", "negative", "neutral"} else "neutral",
        "source_reliability_bp": max(0, min(10_000, reliability_bp)),
        "confirmed_tags": sorted(set(tags or [])),
        "coverage_fields": {},
        "shared_source_group": shared_source_group or f"record:{record_id}",
        "profile_id": None,
        "withdrawn": withdrawn,
        "counterevidence": [],
        "conflicts": sorted(set(conflicts or [])),
        "relationship_confirmation": relationship_confirmation,
        "consent_active": consent_active,
        "profile_dispute_bp": 0,
        "boundary_sensitivity_bp": 0,
        "source_type": source_type,
        "verification_status": verification_status,
    }


def _collect_facts(conn, profile: dict) -> tuple[list[dict], list[dict]]:
    profile_id = profile["id"]
    birth_time = _pg().provider.decrypt(profile["birth_time_ciphertext"]).decode() if profile["birth_time_ciphertext"] else ""
    birth_place = _dec(profile["birth_location_ciphertext"], {})
    facts = [{
        "record_id": str(profile_id),
        "dimension_id": "lx_ming",
        "fact_kind": "coverage",
        "occurred_on": None,
        "date_precision": "unknown",
        "state": "coverage",
        "direction": "neutral",
        "source_reliability_bp": 10000,
        "confirmed_tags": [],
        "coverage_fields": {
            "birth_date": bool(profile["birth_date_ciphertext"]),
            "birth_time_precision": profile["birth_time_precision"] != "unknown" and bool(birth_time),
            "birth_place": bool(birth_place),
            "timezone": bool(profile["timezone"]),
        },
        "shared_source_group": f"record:{profile_id}",
        "profile_id": str(profile_id),
        "withdrawn": False,
        "counterevidence": [],
        "conflicts": [],
        "relationship_confirmation": "not_applicable",
        "consent_active": True,
        "profile_dispute_bp": 0,
        "boundary_sensitivity_bp": 0,
        "source_type": "profile_coverage",
        "verification_status": "user_confirmed",
    }]
    refs = [{
        "record_id": str(profile_id), "record_table": "profiles",
        "dimension_id": "lx_ming", "fact_kind": "coverage",
        "withdrawn": False, "record_revision": str(profile["updated_at"]),
    }]
    rows = conn.execute(
        """SELECT * FROM evidence_items
           WHERE profile_id=%s AND deleted_at IS NULL ORDER BY id""",
        (profile_id,),
    ).fetchall()
    for row in rows:
        dimension = DOMAIN_DIMENSIONS.get(row["domain"])
        if not dimension:
            continue
        structured = _dec(row["structured_payload_encrypted"], {})
        status = row["status"]
        fact = _record_fact(
            record_id=row["id"],
            dimension_id=dimension,
            occurred_on=row["event_occurred_at"] or row["observed_from"],
            state=str(structured.get("state") or ("confirmed_tag" if dimension == "lx_meng" else "observed")),
            direction=str(structured.get("direction", "positive")),
            tags=structured.get("confirmed_tags", []) if isinstance(structured.get("confirmed_tags", []), list) else [],
            reliability_bp=int((row["reliability_score"] or 0) * 10_000),
            shared_source_group=(
                f"event:{structured['event_group_id']}"
                if isinstance(structured.get("event_group_id"), str)
                and structured["event_group_id"] else None
            ),
            withdrawn=status == "withdrawn",
            source_type=str(row["source_type"] or "user_record"),
            verification_status="user_confirmed" if status == "confirmed" else "user_draft",
            conflicts=["record_disputed"] if status == "disputed" else [],
        )
        # Draft records provide coverage but never strength.
        if status not in {"confirmed", "disputed", "withdrawn"}:
            fact["fact_kind"] = "coverage"
            fact["direction"] = "neutral"
        facts.append(fact)
        refs.append({
            "record_id": str(row["id"]), "record_table": "evidence_items",
            "dimension_id": dimension, "fact_kind": fact["fact_kind"],
            "withdrawn": status == "withdrawn", "record_revision": str(row["updated_at"]),
        })
    journals = conn.execute(
        """SELECT * FROM journal_entries
           WHERE profile_id=%s AND deleted_at IS NULL AND candidate_evidence
           ORDER BY id""",
        (profile_id,),
    ).fetchall()
    for row in journals:
        dimension = JOURNAL_DIMENSIONS.get(row["entry_type"])
        if not dimension:
            continue
        fields = _dec(row["structured_payload_encrypted"], {})
        tags = _dec(row["tags_encrypted"], [])
        facts.append(_record_fact(
            record_id=row["id"], dimension_id=dimension, occurred_on=row["entry_date"],
            state=str(fields.get("state", "observed")),
            direction=str(fields.get("direction", "positive")),
            tags=tags if dimension == "lx_meng" else [],
            reliability_bp=6500,
            shared_source_group=(
                f"event:{fields['event_group_id']}"
                if isinstance(fields.get("event_group_id"), str)
                and fields["event_group_id"] else None
            ),
        ))
        refs.append({
            "record_id": str(row["id"]), "record_table": "journal_entries",
            "dimension_id": dimension, "fact_kind": "evidence",
            "withdrawn": False, "record_revision": str(row["updated_at"]),
        })
    events = conn.execute(
        """SELECT * FROM life_events WHERE profile_id=%s AND deleted_at IS NULL ORDER BY id""",
        (profile_id,),
    ).fetchall()
    for row in events:
        facts.append(_record_fact(
            record_id=row["id"], dimension_id="lx_shi", occurred_on=row["occurred_from"],
            state="user_reported", reliability_bp=7000,
        ))
        refs.append({
            "record_id": str(row["id"]), "record_table": "life_events",
            "dimension_id": "lx_shi", "fact_kind": "evidence",
            "withdrawn": False, "record_revision": str(row["updated_at"]),
        })
    relations = conn.execute(
        """SELECT r.*,
          EXISTS(SELECT 1 FROM relationship_consents c WHERE c.subject_id=r.id
            AND c.consent_status='granted' AND c.withdrawn_at IS NULL
            AND (c.expires_at IS NULL OR c.expires_at>now())) AS consent_active
          FROM relationship_subjects r WHERE r.profile_id=%s ORDER BY r.id""",
        (profile_id,),
    ).fetchall()
    for row in relations:
        mutual = row["mode"] == "consented_profile" and row["consent_active"]
        facts.append(_record_fact(
            record_id=row["id"], dimension_id="lx_yuan_relation",
            occurred_on=row["created_at"], state="interaction",
            reliability_bp=7500 if mutual else 5500,
            relationship_confirmation="mutual" if mutual else "single_party",
            consent_active=row["mode"] == "anonymous_event" or bool(row["consent_active"]),
        ))
        refs.append({
            "record_id": str(row["id"]), "record_table": "relationship_subjects",
            "dimension_id": "lx_yuan_relation", "fact_kind": "evidence",
            "withdrawn": bool(row["consent_revoked_at"]), "record_revision": str(row["created_at"]),
        })
    bazi_runs = conn.execute(
        """SELECT * FROM bazi_research_runs
           WHERE profile_record_id=%s AND deleted_at IS NULL ORDER BY id""",
        (profile_id,),
    ).fetchall()
    bazi_profile_dispute = 4000 if len({row["method_profile_id"] for row in bazi_runs}) > 1 else 0
    for row in bazi_runs:
        engine_result = _dec(row["engine_result_encrypted"], {})
        candidates = (
            engine_result.get("module_results", {}).get("bazi", {})
            .get("result", {}).get("candidates", [])
        )
        boundary_sensitive = any(
            any(bool(flag) for flag in candidate.get("boundary_flags", {}).values())
            for candidate in candidates
        )
        fact = _record_fact(
            record_id=row["id"], dimension_id="lx_ming", occurred_on=row["created_at"],
            state="mechanical_bazi_reference", direction="neutral", reliability_bp=10000,
            source_type="bazi_mechanical_run", verification_status="mechanical_research",
        )
        fact.update({
            "fact_kind": "structural",
            "profile_id": row["method_profile_id"],
            "profile_dispute_bp": bazi_profile_dispute,
            "boundary_sensitivity_bp": 4000 if boundary_sensitive else 0,
        })
        facts.append(fact)
        refs.append({
            "record_id": str(row["id"]), "record_table": "bazi_research_runs",
            "dimension_id": "lx_ming", "fact_kind": "structural",
            "withdrawn": False, "record_revision": row["output_hash"],
        })
    ziwei_runs = conn.execute(
        """SELECT * FROM ziwei_research_runs
           WHERE profile_record_id=%s AND deleted_at IS NULL ORDER BY id""",
        (profile_id,),
    ).fetchall()
    ziwei_profile_dispute = 4000 if len({row["method_profile_id"] for row in ziwei_runs}) > 1 else 0
    for row in ziwei_runs:
        fact = _record_fact(
            record_id=row["id"], dimension_id="lx_ming", occurred_on=row["created_at"],
            state="mechanical_ziwei_reference", direction="neutral", reliability_bp=10000,
            source_type="ziwei_mechanical_run", verification_status="mechanical_research",
        )
        fact.update({
            "fact_kind": "structural",
            "profile_id": row["method_profile_id"],
            "profile_dispute_bp": ziwei_profile_dispute,
        })
        facts.append(fact)
        refs.append({
            "record_id": str(row["id"]), "record_table": "ziwei_research_runs",
            "dimension_id": "lx_ming", "fact_kind": "structural",
            "withdrawn": False, "record_revision": row["output_hash"],
        })
    return facts, refs


def _request(profile_id: UUID, facts: list[dict], excluded: list[str], run_id: UUID, as_of: str) -> dict:
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": str(run_id),
        "run_mode": "research_preview",
        "requested_modules": ["signals", "inference"],
        "input_snapshot": {
            "operation": "run_liuxiang_evidence_v1",
            "subject_id": str(profile_id),
            "facts": facts,
            "excluded_record_ids": sorted(set(excluded)),
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
    return [{
        "dimension_id": item["dimension_id"],
        "rank": item["rank"],
        "strength_bp": item["calibrated_strength_bp"],
        "confidence_bp": item["confidence_bp"],
        "status": item["status"],
        "support_count": len(item["supporting_signal_ids"]),
        "counterevidence_count": len(item["counterevidence_signal_ids"]),
        "missing_facts": item["missing_facts"],
    } for item in domain["candidates"]]


def _stored(conn, execution_id: UUID) -> tuple[dict, dict, dict]:
    row = conn.execute(
        "SELECT * FROM liuxiang_user_executions WHERE id=%s", (execution_id,)
    ).fetchone()
    if not row:
        raise HTTPException(404, "liuxiang_execution_not_found")
    return row, _dec(row["input_snapshot_encrypted"], {}), _dec(row["result_encrypted"], {})


def _persist_execution(
    conn, user: dict, profile_id: UUID, request: dict, result: dict, refs: list[dict],
    *, kind: str, parent_execution_id: UUID | None, title: str,
) -> tuple[UUID, UUID]:
    run_id = UUID(request["run_id"])
    domain = result["module_results"]["inference"]["result"]
    summary = _summary(result)
    conn.execute(
        """INSERT INTO liuxiang_user_executions(
          id,owner_id,profile_id,parent_execution_id,execution_kind,
          input_snapshot_encrypted,result_encrypted,candidate_summary,
          engine_version,ruleset_bundle_id,ruleset_bundle_hash,
          evidence_policy_id,evidence_policy_version,evidence_policy_hash,
          profile_version,input_hash,output_hash,trace_hash,replay_manifest,status,research_notice
        ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            run_id, user["id"], profile_id, parent_execution_id, kind,
            _enc(request), _enc(result), json.dumps(summary), result["engine_version"],
            result["ruleset_bundle_id"], result["ruleset_bundle_hash"],
            domain["evidence_policy_id"], domain["evidence_policy_version"],
            domain["evidence_policy_hash"], "profile/current",
            result["input_hash"], result["output_hash"], result["trace_hash"],
            json.dumps(result["replay_manifest"]), domain["status"], NOTICE,
        ),
    )
    selected = set(domain.get("evidence_selection", {}).get("selected_record_ids", []))
    for ref in refs:
        record_id = UUID(ref["record_id"])
        fingerprint = _hash({
            "record_id": ref["record_id"], "record_table": ref["record_table"],
            "record_revision": ref["record_revision"], "dimension_id": ref["dimension_id"],
        })
        conn.execute(
            """INSERT INTO liuxiang_execution_evidence_refs(
              execution_id,owner_id,record_id,record_table,dimension_id,fact_kind,
              included,withdrawn_at_run,record_revision,source_fingerprint
            ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                run_id, user["id"], record_id, ref["record_table"], ref["dimension_id"],
                ref["fact_kind"], ref["record_id"] in selected or ref["fact_kind"] != "evidence",
                ref["withdrawn"], ref["record_revision"], fingerprint,
            ),
        )
    archive_id = uuid7()
    parent_entry_id = None
    if parent_execution_id is not None:
        parent_row = conn.execute(
            "SELECT id FROM sanji_archive_entries WHERE execution_id=%s ORDER BY created_at LIMIT 1",
            (parent_execution_id,),
        ).fetchone()
        parent_entry_id = parent_row["id"] if parent_row else None
    conn.execute(
        """INSERT INTO sanji_archive_entries(
          id,owner_id,profile_id,execution_id,parent_entry_id,entry_type,title_ciphertext,
          original_record_refs,status,candidate_summary,engine_version,ruleset_version,
          evidence_policy_version,profile_version,output_hash,trace_hash,replay_available,
          research_notice
        ) VALUES(%s,%s,%s,%s,%s,'liuxiang_research',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true,%s)""",
        (
            archive_id, user["id"], profile_id, run_id, parent_entry_id, _enc(title),
            json.dumps([{"record_id": r["record_id"], "record_table": r["record_table"]} for r in refs]),
            domain["status"], json.dumps(summary), result["engine_version"],
            domain["ruleset_version"], domain["evidence_policy_version"], "profile/current",
            result["output_hash"], result["trace_hash"], NOTICE,
        ),
    )
    return run_id, archive_id


@router.get("/profiles/{profile_id}/liuxiang/coverage")
def coverage(profile_id: UUID, token: str | None = Cookie(None, alias="__Host-session")):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        profile = _owned_profile(conn, profile_id, user["id"])
        facts, _ = _collect_facts(conn, profile)
    counts = {dimension: 0 for dimension in DOMAIN_DIMENSIONS.values()}
    for fact in facts:
        if fact["fact_kind"] == "evidence" and not fact["withdrawn"]:
            counts[fact["dimension_id"]] += 1
    return {"profile_id": str(profile_id), "channels": counts, "research_notice": NOTICE}


@router.get("/profiles/{profile_id}/liuxiang/evidence")
def selectable_evidence(profile_id: UUID, token: str | None = Cookie(None, alias="__Host-session")):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        facts, refs = _collect_facts(conn, _owned_profile(conn, profile_id, user["id"]))
    by_id = {fact["record_id"]: fact for fact in facts}
    return {"items": [{
        "record_id": ref["record_id"], "record_table": ref["record_table"],
        "dimension_id": ref["dimension_id"], "fact_kind": ref["fact_kind"],
        "withdrawn": ref["withdrawn"], "date_precision": by_id[ref["record_id"]]["date_precision"],
        "state": by_id[ref["record_id"]]["state"],
    } for ref in refs], "private_text_included": False}


@router.post("/profiles/{profile_id}/liuxiang/executions", status_code=201)
def create_execution(
    profile_id: UUID, payload: dict = Body(default={}),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    pg, user = _pg(), _user(token)
    excluded = payload.get("excluded_record_ids", [])
    if not isinstance(excluded, list) or any(not isinstance(value, str) for value in excluded):
        raise HTTPException(422, "excluded_record_ids_must_be_array")
    as_of = str(payload.get("as_of") or datetime.now(timezone.utc).isoformat())
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/profiles/{id}/liuxiang/executions",
            key, pg.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        profile = _owned_profile(conn, profile_id, user["id"])
        facts, refs = _collect_facts(conn, profile)
        run_id = uuid7()
        request = _request(profile_id, facts, excluded, run_id, as_of)
        try:
            result = execute(request)
        except ValueError as exc:
            raise HTTPException(422, exc.as_dict() if hasattr(exc, "as_dict") else str(exc)) from exc
        execution_id, archive_id = _persist_execution(
            conn, user, profile_id, request, result, refs,
            kind="initial", parent_execution_id=None,
            title=str(payload.get("title") or "六象研究记录"),
        )
        domain = result["module_results"]["inference"]["result"]
        response = {
            "id": str(execution_id), "archive_id": str(archive_id),
            "status": domain["status"], "strength_bp": domain["strength_bp"],
            "confidence_bp": domain["confidence_bp"], "candidates": _summary(result),
            "output_hash": result["output_hash"], "trace_hash": result["trace_hash"],
            "research_notice": NOTICE,
        }
        pg.complete(conn, claim, key, 201, response)
        return response


@router.get("/liuxiang/executions/{execution_id}")
def get_execution(execution_id: UUID, token: str | None = Cookie(None, alias="__Host-session")):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        row, _, result = _stored(conn, execution_id)
        return {
            "id": str(row["id"]), "profile_id": str(row["profile_id"]),
            "status": row["status"], "candidates": row["candidate_summary"],
            "result": result["module_results"]["inference"]["result"],
            "output_hash": row["output_hash"], "trace_hash": row["trace_hash"],
            "created_at": row["created_at"], "research_notice": row["research_notice"],
        }


@router.get("/liuxiang/executions/{execution_id}/evidence")
def execution_evidence(execution_id: UUID, token: str | None = Cookie(None, alias="__Host-session")):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        _stored(conn, execution_id)
        rows = conn.execute(
            """SELECT record_id,record_table,dimension_id,fact_kind,included,
               withdrawn_at_run,record_revision,source_fingerprint
               FROM liuxiang_execution_evidence_refs WHERE execution_id=%s
               ORDER BY dimension_id,record_table,record_id""",
            (execution_id,),
        ).fetchall()
        return {"items": [{**row, "record_id": str(row["record_id"])} for row in rows],
                "private_text_included": False}


@router.post("/liuxiang/executions/{execution_id}/replay")
def replay_execution(
    execution_id: UUID,
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/liuxiang/executions/{id}/replay",
            key, pg.fingerprint({"execution_id": str(execution_id)}),
        )
        if isinstance(claim, dict):
            return claim
        row, request, original = _stored(conn, execution_id)
        reproduced = replay(row["replay_manifest"], request)
        matched = (
            reproduced["output_hash"] == original["output_hash"]
            and reproduced["trace_hash"] == original["trace_hash"]
        )
        conn.execute(
            """INSERT INTO liuxiang_replay_records(
              id,owner_id,execution_id,replay_output_hash,replay_trace_hash,matched
            ) VALUES(%s,%s,%s,%s,%s,%s)""",
            (uuid7(), user["id"], execution_id, reproduced["output_hash"], reproduced["trace_hash"], matched),
        )
        response = {"execution_id": str(execution_id), "matched": matched,
                    "output_hash": reproduced["output_hash"], "trace_hash": reproduced["trace_hash"]}
        pg.complete(conn, claim, key, 200, response)
        return response


@router.post("/liuxiang/executions/{execution_id}/reanalyze", status_code=201)
def reanalyze(
    execution_id: UUID, payload: dict = Body(default={}),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/liuxiang/executions/{id}/reanalyze",
            key, pg.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        parent, _, _ = _stored(conn, execution_id)
        profile = _owned_profile(conn, parent["profile_id"], user["id"])
        facts, refs = _collect_facts(conn, profile)
        run_id = uuid7()
        request = _request(
            profile["id"], facts, payload.get("excluded_record_ids", []), run_id,
            str(payload.get("as_of") or datetime.now(timezone.utc).isoformat()),
        )
        result = execute(request)
        new_id, archive_id = _persist_execution(
            conn, user, profile["id"], request, result, refs,
            kind="reanalysis", parent_execution_id=execution_id,
            title=str(payload.get("title") or "六象重新分析"),
        )
        response = {"id": str(new_id), "archive_id": str(archive_id),
                    "parent_execution_id": str(execution_id), "creates_new_record": True}
        pg.complete(conn, claim, key, 201, response)
        return response


def _comparison(left: dict, right: dict, left_request: dict, right_request: dict) -> dict:
    # Use record IDs rather than full fact equality so no private facts are copied.
    left_records = {item["record_id"] for item in left_request["input_snapshot"].get("facts", [])}
    right_records = {item["record_id"] for item in right_request["input_snapshot"].get("facts", [])}
    return {
        "input_records_added": sorted(right_records - left_records),
        "input_records_removed_or_withdrawn": sorted(left_records - right_records),
        "evidence_policy_changed": left["evidence_policy_hash"] != right["evidence_policy_hash"],
        "ruleset_changed": left["ruleset_bundle_hash"] != right["ruleset_bundle_hash"],
        "engine_changed": left["engine_version"] != right["engine_version"],
        "profile_changed": left["profile_version"] != right["profile_version"],
        "execution_context_changed": (
            left_request.get("deterministic_context")
            != right_request.get("deterministic_context")
        ),
        "data_precision_changed": _hash([
            (item["record_id"], item.get("date_precision"))
            for item in left_request["input_snapshot"].get("facts", [])
        ]) != _hash([
            (item["record_id"], item.get("date_precision"))
            for item in right_request["input_snapshot"].get("facts", [])
        ]),
        "output_changed": left["output_hash"] != right["output_hash"],
    }


@router.post("/liuxiang/executions/compare")
def compare_executions(
    payload: dict = Body(...),
    key: str = Header(alias="Idempotency-Key"),
    token: str | None = Cookie(None, alias="__Host-session"),
):
    pg, user = _pg(), _user(token)
    try:
        left_id, right_id = UUID(payload["left_execution_id"]), UUID(payload["right_execution_id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(422, "two_execution_ids_required") from exc
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = pg.idempotency(
            conn, user["id"], "POST", "/api/v1/liuxiang/executions/compare",
            key, pg.fingerprint(payload),
        )
        if isinstance(claim, dict):
            return claim
        left, left_request, _ = _stored(conn, left_id)
        right, right_request, _ = _stored(conn, right_id)
        if left["profile_id"] != right["profile_id"]:
            raise HTTPException(409, "executions_must_share_profile")
        summary = _comparison(left, right, left_request, right_request)
        comparison_hash = _hash(summary)
        comparison_id = uuid7()
        conn.execute(
            """INSERT INTO liuxiang_execution_comparisons(
              id,owner_id,left_execution_id,right_execution_id,difference_summary,comparison_hash
            ) VALUES(%s,%s,%s,%s,%s,%s)""",
            (comparison_id, user["id"], left_id, right_id, json.dumps(summary), comparison_hash),
        )
        response = {"id": str(comparison_id), "differences": summary, "comparison_hash": comparison_hash}
        pg.complete(conn, claim, key, 200, response)
        return response


@router.get("/chronicle")
def list_archive(
    profile_id: UUID | None = None,
    token: str | None = Cookie(None, alias="__Host-session"),
):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        rows = conn.execute(
            """SELECT id,profile_id,execution_id,entry_type,status,candidate_summary,
               replay_available,created_at,title_ciphertext,withdrawn_at
               FROM sanji_archive_entries
               WHERE (%s::uuid IS NULL OR profile_id=%s)
               ORDER BY created_at DESC""",
            (profile_id, profile_id),
        ).fetchall()
        return {"items": [{
            "id": str(row["id"]), "profile_id": str(row["profile_id"]),
            "execution_id": str(row["execution_id"]) if row["execution_id"] else None,
            "entry_type": row["entry_type"], "title": _dec(row["title_ciphertext"], ""),
            "status": row["status"], "candidate_summary": row["candidate_summary"],
            "replay_available": row["replay_available"], "created_at": row["created_at"],
            "withdrawn": row["withdrawn_at"] is not None,
        } for row in rows]}


@router.get("/chronicle/{entry_id}")
def get_archive(entry_id: UUID, token: str | None = Cookie(None, alias="__Host-session")):
    pg, user = _pg(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        row = conn.execute("SELECT * FROM sanji_archive_entries WHERE id=%s", (entry_id,)).fetchone()
        if not row:
            raise HTTPException(404, "archive_entry_not_found")
        return {
            "id": str(row["id"]), "profile_id": str(row["profile_id"]),
            "execution_id": str(row["execution_id"]) if row["execution_id"] else None,
            "entry_type": row["entry_type"], "title": _dec(row["title_ciphertext"], ""),
            "note": _dec(row["note_ciphertext"], ""), "status": row["status"],
            "candidate_summary": row["candidate_summary"], "engine_version": row["engine_version"],
            "ruleset_version": row["ruleset_version"],
            "evidence_policy_version": row["evidence_policy_version"],
            "output_hash": row["output_hash"], "trace_hash": row["trace_hash"],
            "replay_available": row["replay_available"], "research_notice": row["research_notice"],
            "created_at": row["created_at"],
        }
