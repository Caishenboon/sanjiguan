"""Sprint 1B-1 evidence-capture API. It deliberately contains no interpretive rules."""
from __future__ import annotations

import hashlib
import json
from uuid import UUID

from fastapi import APIRouter, Cookie, Header, HTTPException, Response
from sanji_engine import execute

from apps.api.app.core.runtime import SESSION_COOKIE_NAME

from apps.api.app.core.ids import uuid7
from apps.api.app.schemas.models import (
    EvidenceCreate, EvidencePatch, JournalCreate, JournalPatch, OnboardingUpdate,
    RelationshipConsentUpdate, RelationshipSubjectCreate, ThreeCoinDivinationCreate,
)
from packages.evidence.completeness import DOMAINS, completeness_state, summarize_completeness
from packages.evidence.reliability import assess_reliability
from packages.evidence.three_coin import (
    COIN_FACE_MAPPING_ID, COIN_FACE_MAPPING_VERSION, validate_six_tosses,
)

router = APIRouter(prefix="/api/v1")


def _deps():
    from apps.api.app import postgres_app as pg
    return pg


def _enc(value: object) -> bytes:
    return _deps().provider.encrypt(
        json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")
    )


def _dec(value: bytes | None, default=None):
    if value is None:
        return default
    return json.loads(_deps().provider.decrypt(value).decode("utf-8"))


def _user(token):
    return _deps().auth(token)


def _claim(conn, user, method, route, key, data):
    pg = _deps()
    return pg.idempotency(conn, user["id"], method, route, key, pg.fingerprint(data))


def _finish(conn, claim, key, status, result):
    _deps().complete(conn, claim, key, status, result)
    return result


@router.put("/profiles/{profile_id}/onboarding")
def save_onboarding(profile_id: UUID, payload: OnboardingUpdate,
                    key: str = Header(alias="Idempotency-Key"),
                    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user, data = _deps(), _user(token), payload.model_dump(mode="json")
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = _claim(conn, user, "PUT", "/api/v1/profiles/{id}/onboarding", key, data)
        if isinstance(claim, dict):
            return claim
        oid = uuid7()
        row = conn.execute(
            """INSERT INTO onboarding_sessions(id,profile_id,current_step,step_states,encrypted_draft)
               VALUES(%s,%s,%s,%s,%s)
               ON CONFLICT(profile_id) DO UPDATE SET current_step=excluded.current_step,
                 step_states=excluded.step_states,encrypted_draft=excluded.encrypted_draft,updated_at=now()
               RETURNING id""",
            (oid, profile_id, data["current_step"], json.dumps(data["step_states"]), _enc(data["draft"])),
        ).fetchone()
        result = {"id": str(row["id"]), "profile_id": str(profile_id), **data}
        return _finish(conn, claim, key, 200, result)


@router.get("/profiles/{profile_id}/onboarding")
def get_onboarding(profile_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user = _deps(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        row = conn.execute("SELECT * FROM onboarding_sessions WHERE profile_id=%s", (profile_id,)).fetchone()
        if not row:
            return {"profile_id": str(profile_id), "current_step": 1, "step_states": {}, "draft": {}}
        return {"id": str(row["id"]), "profile_id": str(profile_id), "current_step": row["current_step"],
                "step_states": row["step_states"], "draft": _dec(row["encrypted_draft"], {})}


def _evidence_result(row):
    payload = _dec(row["payload_encrypted"], {})
    return {
        "id": str(row["id"]), "profile_id": str(row["profile_id"]), "domain": row["domain"],
        "type": row["type"], "title": _dec(row["title_ciphertext"], ""),
        "raw_narrative": payload.get("raw_narrative", ""),
        "structured_payload": _dec(row["structured_payload_encrypted"], {}),
        "reliability_score": float(row["reliability_score"]),
        "reliability_level": row["reliability_level"], "status": row["status"],
        "event_occurred_at": row["event_occurred_at"], "recorded_at": row["recorded_at"],
        "reliability_meaning": "record_reliability_only_not_past_life_evidence",
    }


@router.post("/profiles/{profile_id}/evidence", status_code=201)
def create_evidence(profile_id: UUID, payload: EvidenceCreate, response: Response,
                    key: str = Header(alias="Idempotency-Key"),
                    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user, data = _deps(), _user(token), payload.model_dump(mode="json")
    reliability = assess_reliability({**data, **data["structured_payload"]})
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = _claim(conn, user, "POST", "/api/v1/profiles/{id}/evidence", key, data)
        if isinstance(claim, dict):
            response.status_code = 201
            return claim
        eid = uuid7()
        conn.execute(
            """INSERT INTO evidence_items(id,profile_id,type,payload_encrypted,observed_from,observed_to,
               frequency,vividness,source_reliability,domain,title_ciphertext,structured_payload_encrypted,
               first_observed_age,intensity,duration_years,source_type,user_confidence,
               independent_corroboration,reliability_score,reliability_level,event_occurred_at)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (eid, profile_id, data["type"], _enc({"raw_narrative": data["raw_narrative"],
             "possible_ordinary_explanations": data["possible_ordinary_explanations"],
             "counterevidence": data["counterevidence"]}), data["observed_from"], data["observed_to"],
             data["frequency"], data["vividness"], reliability["reliability_score"], data["domain"],
             _enc(data["title"]), _enc(data["structured_payload"]), data["first_observed_age"],
             data["intensity"], data["duration_years"], data["source_type"], data["user_confidence"],
             data["independent_corroboration"], reliability["reliability_score"],
             reliability["reliability_level"], data["event_occurred_at"]),
        )
        result = {"id": str(eid), "profile_id": str(profile_id), **data, **reliability}
        return _finish(conn, claim, key, 201, result)


@router.get("/profiles/{profile_id}/evidence")
def list_evidence(profile_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user = _deps(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        rows = conn.execute(
            "SELECT * FROM evidence_items WHERE profile_id=%s AND deleted_at IS NULL ORDER BY recorded_at DESC",
            (profile_id,),
        ).fetchall()
        return {"items": [_evidence_result(row) for row in rows]}


@router.get("/evidence/{evidence_id}")
def get_evidence(evidence_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user = _deps(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        row = conn.execute("SELECT * FROM evidence_items WHERE id=%s AND deleted_at IS NULL",
                           (evidence_id,)).fetchone()
        if not row:
            raise HTTPException(404, "evidence_not_found")
        return _evidence_result(row)


@router.patch("/evidence/{evidence_id}")
def patch_evidence(evidence_id: UUID, payload: EvidencePatch,
                   key: str = Header(alias="Idempotency-Key"),
                   token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user, data = _deps(), _user(token), payload.model_dump(mode="json", exclude_unset=True)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = _claim(conn, user, "PATCH", "/api/v1/evidence/{id}", key, data)
        if isinstance(claim, dict):
            return claim
        row = conn.execute("SELECT * FROM evidence_items WHERE id=%s AND deleted_at IS NULL FOR UPDATE",
                           (evidence_id,)).fetchone()
        if not row:
            raise HTTPException(404, "evidence_not_found")
        revision = conn.execute(
            "SELECT coalesce(max(revision_no),0)+1 AS n FROM evidence_revisions WHERE evidence_id=%s",
            (evidence_id,),
        ).fetchone()["n"]
        conn.execute("INSERT INTO evidence_revisions VALUES(%s,%s,%s,%s,%s,now())",
                     (uuid7(), evidence_id, revision, _enc(_evidence_result(row)), user["id"]))
        raw = _dec(row["payload_encrypted"], {})
        if "raw_narrative" in data:
            raw["raw_narrative"] = data["raw_narrative"]
        if "possible_ordinary_explanations" in data:
            raw["possible_ordinary_explanations"] = data["possible_ordinary_explanations"]
        if "counterevidence" in data:
            raw["counterevidence"] = data["counterevidence"]
        conn.execute(
            """UPDATE evidence_items SET title_ciphertext=coalesce(%s,title_ciphertext),
               payload_encrypted=%s,structured_payload_encrypted=coalesce(%s,structured_payload_encrypted),
               status=coalesce(%s,status),updated_at=now() WHERE id=%s""",
            (_enc(data["title"]) if data.get("title") is not None else None, _enc(raw),
             _enc(data["structured_payload"]) if data.get("structured_payload") is not None else None,
             data.get("status"), evidence_id),
        )
        result = {"id": str(evidence_id), "revision_no": revision, "status": data.get("status", row["status"])}
        return _finish(conn, claim, key, 200, result)


@router.delete("/evidence/{evidence_id}", status_code=202)
def delete_evidence(evidence_id: UUID, key: str = Header(alias="Idempotency-Key"),
                    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user = _deps(), _user(token)
    data = {"id": str(evidence_id)}
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = _claim(conn, user, "DELETE", "/api/v1/evidence/{id}", key, data)
        if isinstance(claim, dict):
            return claim
        if not conn.execute("UPDATE evidence_items SET deleted_at=now() WHERE id=%s AND deleted_at IS NULL",
                            (evidence_id,)).rowcount:
            raise HTTPException(404, "evidence_not_found")
        return _finish(conn, claim, key, 202, {"id": str(evidence_id), "status": "soft_deleted"})


@router.get("/profiles/{profile_id}/completeness")
def profile_completeness(profile_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user = _deps(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        rows = conn.execute(
            """SELECT domain,max(reliability_score) score FROM evidence_items
               WHERE profile_id=%s AND deleted_at IS NULL GROUP BY domain""", (profile_id,)
        ).fetchall()
        scores = {r["domain"]: float(r["score"]) for r in rows}
        onboarding = conn.execute("SELECT step_states FROM onboarding_sessions WHERE profile_id=%s",
                                  (profile_id,)).fetchone()
        states = {}
        for domain in DOMAINS:
            if domain in scores:
                states[domain] = completeness_state("filled", scores[domain])
            else:
                raw = (onboarding or {}).get("step_states", {}).get(domain, "not_filled")
                states[domain] = raw if raw in {"unknown", "explicit_none", "not_applicable"} else "not_filled"
        return summarize_completeness(states)


@router.get("/profiles/{profile_id}/timeline")
def timeline(profile_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user = _deps(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        rows = conn.execute(
            """SELECT id,domain,type,event_occurred_at,recorded_at FROM evidence_items
               WHERE profile_id=%s AND deleted_at IS NULL
               ORDER BY coalesce(event_occurred_at,recorded_at),recorded_at""", (profile_id,)
        ).fetchall()
        return {"items": [{**r, "id": str(r["id"])} for r in rows],
                "meaning": "chronology_only_no_metaphysical_interpretation"}


@router.post("/profiles/{profile_id}/journal", status_code=201)
def create_journal(profile_id: UUID, payload: JournalCreate, response: Response,
                   key: str = Header(alias="Idempotency-Key"),
                   token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user, data = _deps(), _user(token), payload.model_dump(mode="json")
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = _claim(conn, user, "POST", "/api/v1/profiles/{id}/journal", key, data)
        if isinstance(claim, dict):
            response.status_code = 201
            return claim
        jid = uuid7()
        conn.execute(
            """INSERT INTO journal_entries(id,profile_id,entry_date,content_encrypted,tags_encrypted,
               entry_type,structured_payload_encrypted,candidate_evidence)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
            (jid, profile_id, data["entry_date"], _enc(data["free_text"]), _enc(data["tags"]),
             data["entry_type"], _enc(data["fields"]), data["candidate_evidence"]),
        )
        archive_id = uuid7()
        title = str(data["fields"].get("title") or data["entry_type"])
        conn.execute(
            """INSERT INTO sanji_archive_entries(
              id,owner_id,profile_id,entry_type,title_ciphertext,original_record_refs,
              status,candidate_summary,replay_available
            ) VALUES(%s,%s,%s,'record',%s,%s,'recorded','[]'::jsonb,false)""",
            (
                archive_id, user["id"], profile_id, _enc(title),
                json.dumps([{"record_id": str(jid), "record_table": "journal_entries"}]),
            ),
        )
        for eid in data["evidence_ids"]:
            conn.execute("INSERT INTO journal_evidence_links VALUES(%s,%s,now())", (jid, eid))
        return _finish(conn, claim, key, 201, {
            "id": str(jid), "archive_id": str(archive_id), "profile_id": str(profile_id), **data
        })


@router.get("/profiles/{profile_id}/journal")
def list_journal(profile_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user = _deps(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        rows = conn.execute(
            "SELECT * FROM journal_entries WHERE profile_id=%s AND deleted_at IS NULL ORDER BY entry_date DESC",
            (profile_id,),
        ).fetchall()
        return {"items": [{"id": str(r["id"]), "entry_date": r["entry_date"],
                           "entry_type": r["entry_type"], "fields": _dec(r["structured_payload_encrypted"], {}),
                           "free_text": _dec(r["content_encrypted"], ""),
                           "tags": _dec(r["tags_encrypted"], []),
                           "candidate_evidence": r["candidate_evidence"]} for r in rows]}


@router.patch("/journal/{journal_id}")
def patch_journal(journal_id: UUID, payload: JournalPatch,
                  key: str = Header(alias="Idempotency-Key"),
                  token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user, data = _deps(), _user(token), payload.model_dump(mode="json", exclude_unset=True)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = _claim(conn, user, "PATCH", "/api/v1/journal/{id}", key, data)
        if isinstance(claim, dict):
            return claim
        row = conn.execute("SELECT * FROM journal_entries WHERE id=%s AND deleted_at IS NULL",
                           (journal_id,)).fetchone()
        if not row:
            raise HTTPException(404, "journal_not_found")
        changed = {
            "fields": data.get("fields", _dec(row["structured_payload_encrypted"], {})),
            "free_text": data.get("free_text", _dec(row["content_encrypted"], "")),
            "tags": data.get("tags", _dec(row["tags_encrypted"], [])),
            "candidate_evidence": data.get("candidate_evidence", row["candidate_evidence"]),
        }
        conn.execute(
            """UPDATE journal_entries SET structured_payload_encrypted=%s,content_encrypted=%s,
               tags_encrypted=%s,candidate_evidence=%s,updated_at=now() WHERE id=%s""",
            (_enc(changed["fields"]), _enc(changed["free_text"]), _enc(changed["tags"]),
             changed["candidate_evidence"], journal_id),
        )
        return _finish(conn, claim, key, 200, {"id": str(journal_id), **changed})


@router.delete("/journal/{journal_id}", status_code=202)
def delete_journal(journal_id: UUID, key: str = Header(alias="Idempotency-Key"),
                   token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user = _deps(), _user(token)
    data = {"id": str(journal_id)}
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = _claim(conn, user, "DELETE", "/api/v1/journal/{id}", key, data)
        if isinstance(claim, dict):
            return claim
        if not conn.execute("UPDATE journal_entries SET deleted_at=now() WHERE id=%s AND deleted_at IS NULL",
                            (journal_id,)).rowcount:
            raise HTTPException(404, "journal_not_found")
        return _finish(conn, claim, key, 202, {"id": str(journal_id), "status": "soft_deleted"})


IDENTIFYING_KEYS = {"name", "full_name", "phone", "email", "social_account", "exact_address",
                    "id_number", "wechat", "passport"}


@router.post("/profiles/{profile_id}/relationships", status_code=201)
def create_relationship(profile_id: UUID, payload: RelationshipSubjectCreate, response: Response,
                        key: str = Header(alias="Idempotency-Key"),
                        token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user, data = _deps(), _user(token), payload.model_dump(mode="json")
    if data["mode"] == "anonymous_event" and (data.get("alias") or IDENTIFYING_KEYS & set(data["event_payload"])):
        raise HTTPException(422, "anonymous_event_must_not_contain_identifiers")
    if data["mode"] == "pending_consent" and not data.get("linked_profile_id"):
        raise HTTPException(422, "pending_consent_requires_linked_profile")
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = _claim(conn, user, "POST", "/api/v1/profiles/{id}/relationships", key, data)
        if isinstance(claim, dict):
            response.status_code = 201
            return claim
        sid = uuid7()
        consent = _enc({"status": "pending"}) if data["mode"] == "consented_profile" else None
        conn.execute(
            """INSERT INTO relationship_subjects(id,profile_id,mode,linked_profile_id,alias_ciphertext,
               consent_record_encrypted) VALUES(%s,%s,%s,%s,%s,%s)""",
            (sid, profile_id, data["mode"], data.get("linked_profile_id"),
             _enc(data["alias"]) if data.get("alias") else None, consent),
        )
        return _finish(conn, claim, key, 201, {"id": str(sid), "profile_id": str(profile_id),
                                               "mode": data["mode"]})


@router.patch("/relationships/{subject_id}/consent")
def update_relationship_consent(subject_id: UUID, payload: RelationshipConsentUpdate,
                                key: str = Header(alias="Idempotency-Key"),
                                token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user, data = _deps(), _user(token), payload.model_dump(mode="json")
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = _claim(conn, user, "PATCH", "/api/v1/relationships/{id}/consent", key, data)
        if isinstance(claim, dict):
            return claim
        cid = uuid7()
        db_status = {"granted": "active", "withdrawn": "revoked", "expired": "expired"}.get(
            data["consent_status"]
        )
        if db_status is None:
            raise HTTPException(422, "pending_or_anonymous_state_is_recorded_on_relationship_subject")
        proof_type = data["evidence_type"]
        if proof_type == "none":
            raise HTTPException(422, "consent_proof_required")
        record = _enc(data)
        record_hash = hashlib.sha256(record).hexdigest()
        conn.execute(
            """INSERT INTO relationship_consents(id,subject_id,consent_version,status,proof_type,
               scope_json,consented_at,expires_at,revoked_at,record_encrypted,record_hash,created_by)
               VALUES(%s,%s,%s,%s,%s,%s,now(),%s,CASE WHEN %s='revoked' THEN now() END,%s,%s,%s)""",
            (cid, subject_id, data["consent_version"], db_status, proof_type,
             json.dumps(data["scope"]), data["expires_at"], db_status, record, record_hash, user["id"]),
        )
        return _finish(conn, claim, key, 200, {"id": str(cid), "subject_id": str(subject_id),
                                               "consent_status": data["consent_status"]})


@router.post("/profiles/{profile_id}/divinations/three-coin", status_code=201)
def create_three_coin(profile_id: UUID, payload: ThreeCoinDivinationCreate, response: Response,
                      key: str = Header(alias="Idempotency-Key"),
                      token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user, data = _deps(), _user(token), payload.model_dump(mode="json")
    try:
        tosses = validate_six_tosses(data["tosses"])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if (
        data["coin_face_mapping_id"] != COIN_FACE_MAPPING_ID
        or data["coin_face_mapping_version"] != COIN_FACE_MAPPING_VERSION
    ):
        raise HTTPException(422, "coin_face_mapping_version_not_supported")
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        claim = _claim(conn, user, "POST", "/api/v1/profiles/{id}/divinations/three-coin", key, data)
        if isinstance(claim, dict):
            response.status_code = 201
            return claim
        did = uuid7()
        engine_request = {
            "schema_version": "engine-request/1.0.0",
            "engine_api_version": "1.0",
            "run_id": str(did),
            "run_mode": "research_preview",
            "requested_modules": ["yijing"],
            "input_snapshot": {
                "operation": "cast_physical_three_coin",
                "method_id": "YIJING.THREE_COIN.PHYSICAL.MECHANICAL.V1",
                "method_version": "1.0.0",
                "input_order": "bottom_to_top",
                "tosses": [
                    {"line_position": toss["line_no"], "coin_values": toss["coin_values"]}
                    for toss in tosses
                ],
            },
            "ruleset_bundle_id": "yijing-three-coin-mechanical-0.1.0",
            "data_versions": {
                "tzdb": "not_used",
                "ephemeris": "not_used",
                "calendar_dataset": "not_used",
                "yijing_hexagram_mapping": "king-wen-hexagrams/1.0.0",
            },
            "deterministic_context": {
                "as_of": data["divination_at"],
                "random_method": "none",
                "random_seed": None,
            },
        }
        engine_envelope = execute(engine_request)
        engine_result = engine_envelope["module_results"]["yijing"]["result"]
        line_results = {
            line["line_position"]: line for line in engine_result["lines"]
        }
        conn.execute(
            """INSERT INTO divination_sessions(id,profile_id,question_encrypted,purpose_encrypted,
               divination_at,timezone,location_precision,method_id,interrupted_retoss,
               repeated_due_to_dissatisfaction,method_version,coin_face_mapping_id,
               coin_face_mapping_version,engine_result,engine_result_hash,replay_manifest,
               replay_manifest_hash,trace_hash,ruleset_bundle_id,ruleset_bundle_hash,
               mapping_asset_version,research_status)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (did, profile_id, _enc(data["question"]), _enc(data["purpose"]), data["divination_at"],
             data["timezone"], data["location_precision"], data["method_id"], data["interrupted_retoss"],
             data["repeated_due_to_dissatisfaction"], data["method_version"],
             COIN_FACE_MAPPING_ID, COIN_FACE_MAPPING_VERSION, json.dumps(engine_result),
             engine_envelope["replay_manifest"]["domain_result_hashes"]["yijing_domain_hash"],
             json.dumps(engine_envelope["replay_manifest"]),
             engine_envelope["replay_manifest"]["content_hash"], engine_envelope["trace_hash"],
             engine_envelope["ruleset_bundle_id"], engine_envelope["ruleset_bundle_hash"],
             engine_result["mapping_asset"]["asset_version"], "research_active"),
        )
        for toss in tosses:
            line = line_results[toss["line_no"]]
            conn.execute("""INSERT INTO coin_tosses(
              id,divination_session_id,line_no,coin_faces,raw_value,was_retossed,
              created_at,coin_values) VALUES(%s,%s,%s,%s,%s,%s,now(),%s)""",
              (uuid7(), did, toss["line_no"], toss["coin_faces"], line["sum"],
               toss["was_retossed"], toss["coin_values"]))
        archive_id = uuid7()
        conn.execute(
            """INSERT INTO sanji_archive_entries(
              id,owner_id,profile_id,entry_type,title_ciphertext,original_record_refs,
              status,candidate_summary,engine_version,ruleset_version,output_hash,
              trace_hash,replay_available,research_notice
            ) VALUES(%s,%s,%s,'mechanical_result',%s,%s,'recorded','[]'::jsonb,
              %s,%s,%s,%s,false,%s)""",
            (
                archive_id, user["id"], profile_id, _enc(data["question"]),
                json.dumps([{"record_id": str(did), "record_table": "divination_sessions"}]),
                engine_envelope["engine_version"], engine_envelope["ruleset_bundle_id"],
                engine_envelope["output_hash"], engine_envelope["trace_hash"],
                "机械结构；未生成卦义、评分、吉凶或应期。",
            ),
        )
        result = {"id": str(did), "archive_id": str(archive_id),
                  "profile_id": str(profile_id), "method_id": data["method_id"],
                  "method_version": data["method_version"], "tosses": tosses,
                  "coin_face_mapping_id": COIN_FACE_MAPPING_ID,
                  "coin_face_mapping_version": COIN_FACE_MAPPING_VERSION,
                  "engine_result": engine_result,
                  "result_hash": engine_envelope["replay_manifest"]["domain_result_hashes"]["yijing_domain_hash"],
                  "research_status": "research_active",
                  "interpretation": None, "scoring": None,
                  "notice": "仅记录实物三钱结果；未生成卦义、评分或命理结论。"}
        return _finish(conn, claim, key, 201, result)


@router.get("/profiles/{profile_id}/divinations")
def list_divinations(profile_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user = _deps(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        rows = conn.execute(
            """SELECT id,divination_at,timezone,location_precision,method_id,method_version,
               research_status,engine_result_hash
               FROM divination_sessions WHERE profile_id=%s AND deleted_at IS NULL
               ORDER BY divination_at DESC""", (profile_id,)
        ).fetchall()
        return {"items": [{**r, "id": str(r["id"]), "interpretation": None, "scoring": None}
                          for r in rows]}


@router.get("/divinations/{divination_id}")
def get_divination(divination_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    pg, user = _deps(), _user(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        row = conn.execute("SELECT * FROM divination_sessions WHERE id=%s AND deleted_at IS NULL",
                           (divination_id,)).fetchone()
        if not row:
            raise HTTPException(404, "divination_not_found")
        tosses = conn.execute(
            """SELECT line_no,coin_faces,coin_values,raw_value,was_retossed FROM coin_tosses
               WHERE divination_session_id=%s ORDER BY line_no""", (divination_id,)
        ).fetchall()
        return {"id": str(row["id"]), "profile_id": str(row["profile_id"]),
                "question": _dec(row["question_encrypted"], ""), "purpose": _dec(row["purpose_encrypted"], ""),
                "method_id": row["method_id"], "method_version": row["method_version"],
                "coin_face_mapping_id": row["coin_face_mapping_id"],
                "coin_face_mapping_version": row["coin_face_mapping_version"],
                "tosses": tosses, "engine_result": row["engine_result"],
                "result_hash": row["engine_result_hash"],
                "research_status": row["research_status"] or "legacy_method_unknown",
                "interpretation": None, "scoring": None}
