from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from apps.api.app.core.security import normalized_request_id

from apps.api.app.schemas.models import (
    BirthTimeNormalizationResult,
    InvitationAccept,
    NormalizeBirthTimeRequest,
    ProfileCreate,
    ProfilePatch,
    ProfileView,
    SessionView,
    OriginalBirthRecord,
)
from apps.api.app.services.idempotency import find_replay, request_fingerprint, save_result
from apps.api.app.services.store import User, store
from apps.api.app.services.repository import assert_backend_allowed
from packages.engine.normalization import normalize_birth_time

if os.getenv("STORAGE_BACKEND") != "memory":
    raise RuntimeError("storage_backend_must_be_explicit")

app = FastAPI(
    title="Samsara Engine API",
    version="0.1.0-sprint1a",
    description="Engineering foundation only; traditional production rules remain disabled.",
)
assert_backend_allowed(os.getenv("APP_ENV", "development"), store.backend_name)

SESSION_COOKIE = "__Host-session"


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    code = str(exc)
    status = 409 if code == "idempotency_key_conflict" else 422
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code.upper(), "message": code, "request_id": request.state.request_id}},
    )


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = normalized_request_id(request.headers.get("X-Request-ID"))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def current_user(session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE)) -> User:
    user = store.authenticate(session_token)
    if user is None:
        raise HTTPException(status_code=401, detail="authentication_required")
    return user


def require_idempotency_key(value: str | None = Header(default=None, alias="Idempotency-Key")) -> str:
    if value is None or not 16 <= len(value) <= 128:
        raise HTTPException(status_code=400, detail="valid_idempotency_key_required")
    return value


def owned_profile(profile_id: UUID, user: User) -> dict:
    profile = store.profiles.get(profile_id)
    if profile is None or profile["owner_id"] != user.id:
        raise HTTPException(status_code=404, detail="profile_not_found")
    return profile


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "scope": "sprint1a",
        "traditional_rules": "disabled",
        "storage": "memory-development-postgresql-contract",
    }


@app.post("/api/v1/auth/invitations/accept", response_model=SessionView)
def accept_invitation(payload: InvitationAccept, response: Response):
    user, session_token = store.accept_invitation(payload.token)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_token,
        secure=True,
        httponly=True,
        samesite="strict",
        path="/",
        max_age=12 * 3600,
    )
    return SessionView(user_id=user.id, role=user.role)


@app.post("/api/v1/auth/logout", status_code=204)
def logout(
    response: Response,
    _user: User = Depends(current_user),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    store.revoke_session(session_token)
    response.delete_cookie(SESSION_COOKIE, secure=True, httponly=True, samesite="strict", path="/")


@app.get("/api/v1/me", response_model=SessionView)
def me(user: User = Depends(current_user)):
    return SessionView(user_id=user.id, role=user.role)


@app.post("/api/v1/profiles", response_model=ProfileView, status_code=201)
def create_profile(
    payload: ProfileCreate,
    user: User = Depends(current_user),
    key: str = Depends(require_idempotency_key),
):
    route = "POST:/api/v1/profiles"
    fingerprint = request_fingerprint(payload.model_dump(mode="json"))
    replay = find_replay(store, user.id, route, key, fingerprint)
    if replay:
        return replay.response
    now = datetime.now(timezone.utc)
    from apps.api.app.core.ids import uuid7

    profile = {
        **payload.model_dump(),
        "id": uuid7(),
        "owner_id": user.id,
        "created_at": now,
        "updated_at": now,
    }
    store.profiles[profile["id"]] = profile
    serialized = ProfileView.model_validate(profile).model_dump(mode="json")
    save_result(store, user.id, route, key, fingerprint, 201, serialized)
    return profile


@app.get("/api/v1/profiles/{profile_id}", response_model=ProfileView)
def get_profile(profile_id: UUID, user: User = Depends(current_user)):
    return owned_profile(profile_id, user)


@app.patch("/api/v1/profiles/{profile_id}", response_model=ProfileView)
def patch_profile(
    profile_id: UUID,
    payload: ProfilePatch,
    user: User = Depends(current_user),
    key: str = Depends(require_idempotency_key),
):
    route = f"PATCH:/api/v1/profiles/{profile_id}"
    fingerprint = request_fingerprint(payload.model_dump(mode="json", exclude_unset=True))
    replay = find_replay(store, user.id, route, key, fingerprint)
    if replay:
        return replay.response
    profile = owned_profile(profile_id, user)
    changes = payload.model_dump(exclude_unset=True)
    profile.update(changes)
    profile["updated_at"] = datetime.now(timezone.utc)
    serialized = ProfileView.model_validate(profile).model_dump(mode="json")
    save_result(store, user.id, route, key, fingerprint, 200, serialized)
    return profile


@app.delete("/api/v1/profiles/{profile_id}", status_code=202)
def delete_profile(
    profile_id: UUID,
    user: User = Depends(current_user),
    key: str = Depends(require_idempotency_key),
):
    route = f"DELETE:/api/v1/profiles/{profile_id}"
    fingerprint = request_fingerprint({"profile_id": str(profile_id), "action": "delete"})
    replay = find_replay(store, user.id, route, key, fingerprint)
    if replay:
        return replay.response
    owned_profile(profile_id, user)
    result = {"profile_id": str(profile_id), "status": "deletion_queued"}
    save_result(store, user.id, route, key, fingerprint, 202, result)
    return result


@app.post(
    "/api/v1/profiles/{profile_id}/birth-time/normalize",
    response_model=BirthTimeNormalizationResult,
)
def normalize_profile_birth_time(
    profile_id: UUID,
    payload: NormalizeBirthTimeRequest,
    user: User = Depends(current_user),
    key: str = Depends(require_idempotency_key),
):
    route = f"POST:/api/v1/profiles/{profile_id}/birth-time/normalize"
    fingerprint = request_fingerprint(payload.model_dump(mode="json"))
    replay = find_replay(store, user.id, route, key, fingerprint)
    if replay:
        return replay.response
    profile = owned_profile(profile_id, user)
    birth = OriginalBirthRecord.model_validate(profile["birth"])
    result = normalize_birth_time(birth, payload.solar_term_instants_utc)
    serialized = result.model_dump(mode="json")
    save_result(store, user.id, route, key, fingerprint, 200, serialized)
    return result
