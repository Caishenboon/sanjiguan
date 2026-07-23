from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from apps.api.app.core.security import token_hash
from apps.api.app.services.store import IdempotencyRecord, MemoryStore


def request_fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def find_replay(
    data_store: MemoryStore,
    owner_id: UUID,
    route: str,
    idempotency_key: str,
    fingerprint: str,
) -> IdempotencyRecord | None:
    lookup = (owner_id, route, token_hash(idempotency_key))
    record = data_store.idempotency.get(lookup)
    if record is None:
        return None
    if record.expires_at <= datetime.now(timezone.utc):
        data_store.idempotency.pop(lookup, None)
        return None
    if record.request_fingerprint != fingerprint:
        raise ValueError("idempotency_key_conflict")
    return record


def save_result(
    data_store: MemoryStore,
    owner_id: UUID,
    route: str,
    idempotency_key: str,
    fingerprint: str,
    status_code: int,
    response: dict,
) -> None:
    data_store.idempotency[(owner_id, route, token_hash(idempotency_key))] = IdempotencyRecord(
        owner_id=owner_id,
        route=route,
        key_hash=token_hash(idempotency_key),
        request_fingerprint=fingerprint,
        status_code=status_code,
        response=response,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
