from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import psycopg
from fastapi import Cookie, FastAPI, Header, HTTPException, Response
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from apps.api.app.core.encryption import TestKeyProvider, assert_key_provider_allowed
from apps.api.app.core.ids import uuid7
from apps.api.app.core.security import new_token, token_hash
from apps.api.app.schemas.models import InvitationAccept, ProfileCreate, ProfilePatch

SESSION_COOKIE = "__Host-session"
app_env = os.environ.get("APP_ENV", "")
backend = os.environ.get("STORAGE_BACKEND", "")
key_provider_name = os.environ.get("KEY_PROVIDER", "")
if app_env != "test" or backend != "postgres" or key_provider_name != "test-only":
    raise RuntimeError("postgres_test_app_requires_explicit_test_mode")

key_hex = os.environ.get("TEST_ENCRYPTION_KEY_HEX", "")
provider = TestKeyProvider(bytes.fromhex(key_hex))
assert_key_provider_allowed(app_env, provider)
pool = ConnectionPool(os.environ["DATABASE_URL"], min_size=1, max_size=8,
                      kwargs={"row_factory": dict_row}, open=True)
app = FastAPI(title="三际观 PostgreSQL E2E API", version="0.1.6-test")


def fingerprint(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def auth(token: str | None = Cookie(None, alias=SESSION_COOKIE)) -> dict:
    if not token:
        raise HTTPException(401, "authentication_required")
    with pool.connection() as conn:
        row = conn.execute(
            """SELECT u.id,u.role FROM sessions s JOIN users u ON u.id=s.user_id
               WHERE s.token_hash=%s AND s.revoked_at IS NULL AND s.expires_at>now()""",
            (token_hash(token),),
        ).fetchone()
        if not row:
            raise HTTPException(401, "authentication_required")
        return row


def runtime(conn, user: dict):
    conn.execute("SET LOCAL ROLE app_runtime")
    conn.execute("SELECT set_config('app.current_user_id', %s, true)", (str(user["id"]),))
    conn.execute("SELECT set_config('app.current_user_role', %s, true)", (user["role"],))
    conn.execute("SET LOCAL statement_timeout='5s'")


def idempotency(conn, user_id: UUID, method: str, route: str, key: str, request_fp: str):
    kh = token_hash(key)
    row = conn.execute(
        """SELECT request_fingerprint,state,status_code,response_encrypted FROM idempotency_records
           WHERE owner_id=%s AND http_method=%s AND route_template=%s AND key_hash=%s
             AND expires_at>now() FOR UPDATE""", (user_id, method, route, kh)
    ).fetchone()
    if row:
        if row["request_fingerprint"] != request_fp:
            raise HTTPException(409, "idempotency_key_conflict")
        if row["state"] == "completed":
            return json.loads(provider.decrypt(row["response_encrypted"], kh.encode()))
        raise HTTPException(409, "request_in_progress")
    record_id = uuid7()
    conn.execute(
        """INSERT INTO idempotency_records
           (id,owner_id,http_method,route_template,key_hash,request_fingerprint,state,expires_at)
           VALUES(%s,%s,%s,%s,%s,%s,'processing',now()+interval '24 hours')""",
        (record_id, user_id, method, route, kh, request_fp),
    )
    return record_id


def complete(conn, record_id: UUID, key: str, status: int, response_data: dict):
    kh = token_hash(key)
    encrypted = provider.encrypt(json.dumps(response_data).encode(), kh.encode())
    conn.execute(
        """UPDATE idempotency_records SET state='completed',status_code=%s,response_encrypted=%s
           WHERE id=%s""", (status, encrypted, record_id)
    )


@app.get("/healthz")
def health():
    with pool.connection() as conn:
        version = conn.execute("SHOW server_version").fetchone()["server_version"]
    return {"status": "ok", "storage": "postgres", "postgres_version": version}


@app.post("/api/v1/auth/invitations/accept")
def accept(payload: InvitationAccept, response: Response):
    now = datetime.now(timezone.utc)
    with pool.connection() as conn, conn.transaction():
        invite = conn.execute(
            """SELECT * FROM invitations WHERE token_hash=%s AND accepted_at IS NULL
               AND revoked_at IS NULL AND expires_at>now() FOR UPDATE""", (token_hash(payload.token),)
        ).fetchone()
        if not invite:
            raise HTTPException(422, "invalid_or_expired_invitation")
        user_id, session_id, session_token = uuid7(), uuid7(), new_token()
        conn.execute("INSERT INTO users(id,email_ciphertext,role) VALUES(%s,%s,%s)",
                     (user_id, b"test-only", invite["role"]))
        conn.execute("""INSERT INTO sessions(id,user_id,token_hash,expires_at)
                        VALUES(%s,%s,%s,%s)""",
                     (session_id, user_id, token_hash(session_token), now + timedelta(hours=12)))
        conn.execute("UPDATE invitations SET accepted_by=%s,accepted_at=%s WHERE id=%s",
                     (user_id, now, invite["id"]))
    response.set_cookie(SESSION_COOKIE, session_token, secure=True, httponly=True,
                        samesite="strict", path="/")
    return {"user_id": str(user_id), "role": invite["role"]}


@app.post("/api/v1/auth/logout", status_code=204)
def logout(response: Response, token: str | None = Cookie(None, alias=SESSION_COOKIE)):
    user = auth(token)
    with pool.connection() as conn:
        conn.execute("UPDATE sessions SET revoked_at=now() WHERE token_hash=%s AND user_id=%s",
                     (token_hash(token or ""), user["id"]))
        conn.commit()
    response.delete_cookie(SESSION_COOKIE, secure=True, httponly=True, samesite="strict", path="/")


@app.post("/api/v1/profiles", status_code=201)
def create_profile(payload: ProfileCreate, response: Response,
                   key: str = Header(alias="Idempotency-Key"),
                   token: str | None = Cookie(None, alias=SESSION_COOKIE)):
    user = auth(token)
    data = payload.model_dump(mode="json")
    with pool.connection() as conn, conn.transaction():
        runtime(conn, user)
        claim = idempotency(conn, user["id"], "POST", "/api/v1/profiles", key, fingerprint(data))
        if isinstance(claim, dict):
            response.status_code = 201
            return claim
        pid = uuid7()
        birth = data["birth"]
        conn.execute(
            """INSERT INTO profiles(id,owner_id,display_name_ciphertext,timezone,calendar_type,
               birth_date_ciphertext,birth_time_ciphertext,birth_time_precision,
               birth_location_ciphertext,latitude_ciphertext,longitude_ciphertext,consent_version)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (pid, user["id"], provider.encrypt((data["display_name"] or "").encode()),
             birth["timezone_id"], birth["calendar_type"], provider.encrypt(birth["local_date"].encode()),
             provider.encrypt((birth["local_time"] or "").encode()), birth["time_precision"],
             provider.encrypt(json.dumps(birth["place"]).encode()),
             provider.encrypt(str(birth["place"]["latitude"]).encode()),
             provider.encrypt(str(birth["place"]["longitude"]).encode()), data["consent_version"]))
        result = {"id": str(pid), "owner_id": str(user["id"]), **data}
        complete(conn, claim, key, 201, result)
        return result


def fetch_profile(profile_id: UUID, user: dict):
    with pool.connection() as conn, conn.transaction():
        runtime(conn, user)
        row = conn.execute(
            "SELECT id,owner_id,display_name_ciphertext,consent_version,deleted_at FROM profiles WHERE id=%s",
            (profile_id,),
        ).fetchone()
        if not row or row["deleted_at"]:
            raise HTTPException(404, "profile_not_found")
        return {"id": str(row["id"]), "owner_id": str(row["owner_id"]),
                "display_name": provider.decrypt(row["display_name_ciphertext"]).decode(),
                "consent_version": row["consent_version"]}


@app.get("/api/v1/profiles/{profile_id}")
def get_profile(profile_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE)):
    return fetch_profile(profile_id, auth(token))


@app.patch("/api/v1/profiles/{profile_id}")
def patch_profile(profile_id: UUID, payload: ProfilePatch, key: str = Header(alias="Idempotency-Key"),
                  token: str | None = Cookie(None, alias=SESSION_COOKIE)):
    user, data = auth(token), payload.model_dump(mode="json", exclude_unset=True)
    with pool.connection() as conn, conn.transaction():
        runtime(conn, user)
        claim = idempotency(conn, user["id"], "PATCH", "/api/v1/profiles/{id}", key, fingerprint(data))
        if isinstance(claim, dict): return claim
        changed = conn.execute(
            """UPDATE profiles SET display_name_ciphertext=%s,updated_at=now()
               WHERE id=%s AND owner_id=%s AND deleted_at IS NULL""",
            (provider.encrypt((data.get("display_name") or "").encode()), profile_id, user["id"])
        ).rowcount
        if not changed: raise HTTPException(404, "profile_not_found")
        result = {"id": str(profile_id), **data}
        complete(conn, claim, key, 200, result)
        return result


@app.delete("/api/v1/profiles/{profile_id}", status_code=202)
def delete_profile(profile_id: UUID, key: str = Header(alias="Idempotency-Key"),
                   token: str | None = Cookie(None, alias=SESSION_COOKIE)):
    user = auth(token)
    with pool.connection() as conn, conn.transaction():
        runtime(conn, user)
        claim = idempotency(conn, user["id"], "DELETE", "/api/v1/profiles/{id}", key,
                            fingerprint({"id": str(profile_id)}))
        if isinstance(claim, dict): return claim
        changed = conn.execute(
            "UPDATE profiles SET deleted_at=now() WHERE id=%s AND owner_id=%s AND deleted_at IS NULL",
            (profile_id, user["id"])).rowcount
        if not changed: raise HTTPException(404, "profile_not_found")
        result = {"id": str(profile_id), "status": "soft_deleted"}
        complete(conn, claim, key, 202, result)
        return result


from apps.api.app.evidence_routes import router as evidence_router
app.include_router(evidence_router)
from apps.api.app.knowledge_routes import router as knowledge_router
app.include_router(knowledge_router)
from apps.api.app.research_routes import router as research_router
app.include_router(research_router)
