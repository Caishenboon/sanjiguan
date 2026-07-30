"""V1 export and deletion endpoints.

The routes deliberately operate on references and approved projections. They do
not expose encryption material, sessions, idempotency payloads or provider
credentials.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import zipfile
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Cookie, Header, HTTPException
from fastapi.responses import Response

from apps.api.app.core.ids import uuid7

router = APIRouter(prefix="/api/v1")


def _pg():
    from apps.api.app import postgres_app

    return postgres_app


def _json(value):
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(type(value).__name__)


def _manifest_hash(files: dict[str, bytes]) -> str:
    rows = [
        {"name": name, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
        for name, content in sorted(files.items())
    ]
    raw = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def _projection(conn, owner_id: UUID) -> dict:
    profiles = conn.execute(
        """SELECT id,timezone,calendar_type,birth_time_precision,consent_version,
          created_at,updated_at,deleted_at FROM profiles WHERE owner_id=%s ORDER BY id""",
        (owner_id,),
    ).fetchall()
    profile_ids = [row["id"] for row in profiles]
    if not profile_ids:
        return {"profiles": [], "records": [], "relationships": [], "executions": [], "archive": []}
    records = conn.execute(
        """SELECT id,profile_id,entry_date,entry_type,candidate_evidence,created_at,updated_at,
          deleted_at FROM journal_entries WHERE profile_id=ANY(%s) ORDER BY id""",
        (profile_ids,),
    ).fetchall()
    evidence = conn.execute(
        """SELECT id,profile_id,domain,status,source_type,event_occurred_at,recorded_at,
          updated_at,deleted_at FROM evidence_items WHERE profile_id=ANY(%s) ORDER BY id""",
        (profile_ids,),
    ).fetchall()
    relationships = conn.execute(
        """SELECT id,profile_id,mode,linked_profile_id,consented_at,consent_revoked_at,created_at
          FROM relationship_subjects WHERE profile_id=ANY(%s) ORDER BY id""",
        (profile_ids,),
    ).fetchall()
    archive = conn.execute(
        """SELECT id,profile_id,entry_type,status,engine_version,ruleset_version,
          evidence_policy_version,output_hash,trace_hash,replay_available,created_at
          FROM sanji_archive_entries WHERE owner_id=%s ORDER BY created_at,id""",
        (owner_id,),
    ).fetchall()
    executions: list[dict] = []
    for table, kind, hash_column in (
        ("liuxiang_user_executions", "liuxiang", "output_hash"),
        ("topic_executions", "topic", "output_hash"),
        ("life_trend_executions", "life_trend", "core_output_hash"),
    ):
        rows = conn.execute(
            f"""SELECT id,profile_id,status,engine_version,{hash_column} AS output_hash,
              trace_hash,replay_available,created_at FROM {table}
              WHERE owner_id=%s ORDER BY created_at,id""",
            (owner_id,),
        ).fetchall()
        executions.extend({"kind": kind, **dict(row)} for row in rows)
    return {
        "profiles": [dict(row) for row in profiles],
        "records": [dict(row) for row in records],
        "evidence": [dict(row) for row in evidence],
        "relationships": [dict(row) for row in relationships],
        "executions": executions,
        "archive": [dict(row) for row in archive],
        "notice": (
            "Sensitive prose and encryption material are intentionally omitted from this portable "
            "index. Use the encrypted database backup for full-fidelity private migration."
        ),
    }


@router.post("/exports", response_class=Response)
def create_export(
    token: str | None = Cookie(None, alias="__Host-session"),
    _key: str = Header(alias="Idempotency-Key"),
):
    pg, user = _pg(), _pg().auth(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        exported = _projection(conn, user["id"])
        generated = datetime.now(timezone.utc)
        data = json.dumps(exported, ensure_ascii=False, sort_keys=True, default=_json, indent=2).encode()
        report = (
            "# 三际观个人资料导出\n\n"
            f"- 导出时间：{generated.isoformat()}\n"
            f"- 主体：{len(exported['profiles'])}\n"
            f"- 记录：{len(exported['records'])}\n"
            f"- 推演执行：{len(exported['executions'])}\n"
            f"- 三际录：{len(exported['archive'])}\n\n"
            "本报告区分直接记录、机械结构与研究推演；研究态结果不代表已验证事实。\n"
        ).encode("utf-8")
        files = {"data.json": data, "report.md": report}
        manifest = {
            "schema_version": "sanji-export/1.0",
            "generated_at": generated.isoformat(),
            "expires_at": (generated + timedelta(minutes=15)).isoformat(),
            "files": [
                {"path": name, "sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
                for name, value in sorted(files.items())
            ],
            "engine_policy": "versions_and_hashes_preserved",
            "deleted_content": "reported_as_missing; never reconstructed",
        }
        files["manifest.json"] = json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, indent=2
        ).encode()
        export_hash = _manifest_hash(files)
        conn.execute(
            """INSERT INTO user_export_jobs(
              id,owner_id,export_format,manifest_hash,file_count,expires_at
            ) VALUES(%s,%s,'archive_zip',%s,%s,now()+interval '15 minutes')""",
            (uuid7(), user["id"], export_hash, len(files)),
        )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            archive.writestr(name, content)
    return Response(
        output.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=sanjiguan-export.zip",
            "X-Export-Manifest-Hash": export_hash,
            "Cache-Control": "no-store",
        },
    )


@router.delete("/exports/{export_id}", status_code=204)
def revoke_export(
    export_id: UUID,
    token: str | None = Cookie(None, alias="__Host-session"),
    _key: str = Header(alias="Idempotency-Key"),
):
    pg, user = _pg(), _pg().auth(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        changed = conn.execute(
            "UPDATE user_export_jobs SET revoked_at=now() WHERE id=%s AND owner_id=%s AND revoked_at IS NULL",
            (export_id, user["id"]),
        ).rowcount
        if not changed:
            raise HTTPException(404, "export_not_found")


@router.delete("/private-records/{record_type}/{record_id}", status_code=202)
def delete_private_record(
    record_type: str,
    record_id: UUID,
    purge: bool = False,
    token: str | None = Cookie(None, alias="__Host-session"),
    _key: str = Header(alias="Idempotency-Key"),
):
    pg, user = _pg(), _pg().auth(token)
    policies = {
        "journal": ("journal_entries", "id", "deleted_at"),
        "evidence": ("evidence_items", "id", "deleted_at"),
        "life-event": ("life_events", "id", "deleted_at"),
        "relationship": ("relationship_subjects", "id", None),
    }
    if record_type not in policies:
        raise HTTPException(422, "unsupported_record_type")
    table, key_column, deleted_column = policies[record_type]
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        if purge:
            changed = conn.execute(f"DELETE FROM {table} WHERE {key_column}=%s", (record_id,)).rowcount
            mode, impact = "purge", "replay_unavailable"
        elif deleted_column:
            changed = conn.execute(
                f"UPDATE {table} SET {deleted_column}=now() WHERE {key_column}=%s AND {deleted_column} IS NULL",
                (record_id,),
            ).rowcount
            mode, impact = "soft_delete", "historical_snapshot"
        else:
            changed = conn.execute(
                "UPDATE relationship_subjects SET consent_revoked_at=now() WHERE id=%s",
                (record_id,),
            ).rowcount
            mode, impact = "withdraw", "historical_snapshot"
        if not changed:
            raise HTTPException(404, "private_record_not_found")
        conn.execute(
            """INSERT INTO private_deletion_events(
              id,owner_id,resource_type,resource_id,deletion_mode,replay_impact
            ) VALUES(%s,%s,%s,%s,%s,%s)""",
            (uuid7(), user["id"], "relationship" if record_type == "relationship" else "record",
             record_id, mode, impact),
        )
    return {"record_id": str(record_id), "mode": mode, "replay_impact": impact}


@router.delete("/life-trend-executions/{execution_id}/ai-narrative", status_code=202)
def delete_ai_narrative(
    execution_id: UUID,
    token: str | None = Cookie(None, alias="__Host-session"),
    _key: str = Header(alias="Idempotency-Key"),
):
    pg, user = _pg(), _pg().auth(token)
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        changed = conn.execute(
            """UPDATE life_trend_executions SET ai_narrative_encrypted=NULL,
              narrative_output_hash=NULL,ai_status='not_requested',ai_provider=NULL,
              ai_model=NULL,prompt_version=NULL,ai_generated_at=NULL
              WHERE id=%s AND owner_id=%s""",
            (execution_id, user["id"]),
        ).rowcount
        if not changed:
            raise HTTPException(404, "life_trend_execution_not_found")
        conn.execute(
            """INSERT INTO private_deletion_events(
              id,owner_id,resource_type,resource_id,deletion_mode,replay_impact
            ) VALUES(%s,%s,'ai_narrative',%s,'purge','none')""",
            (uuid7(), user["id"], execution_id),
        )
    return {"execution_id": str(execution_id), "ai_narrative": "deleted"}


@router.delete("/account", status_code=202)
def delete_account(
    confirmation: str = Header(alias="X-Delete-Confirmation"),
    token: str | None = Cookie(None, alias="__Host-session"),
    _key: str = Header(alias="Idempotency-Key"),
):
    pg, user = _pg(), _pg().auth(token)
    if confirmation != "DELETE MY SANJIGUAN DATA":
        raise HTTPException(422, "account_deletion_confirmation_required")
    with pg.pool.connection() as conn, conn.transaction():
        pg.runtime(conn, user)
        conn.execute("SELECT purge_current_account(%s,%s)", (user["id"], uuid7()))
    return {"status": "deleted", "replay": "unavailable_after_private_data_purge"}
