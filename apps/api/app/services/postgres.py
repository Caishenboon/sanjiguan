from __future__ import annotations

import json
import hashlib
from contextlib import contextmanager
from typing import Iterator
from uuid import UUID
from datetime import datetime, timedelta, timezone

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


class PostgresRepository:
    """PostgreSQL 16 adapter with bounded pool and transaction-scoped RLS identity."""

    backend_name = "postgres"

    def __init__(self, dsn: str, *, min_size: int = 1, max_size: int = 8, timeout: float = 5,
                 force_runtime_role: bool = False):
        self.force_runtime_role = force_runtime_role
        self.pool = ConnectionPool(
            conninfo=dsn,
            min_size=min_size,
            max_size=max_size,
            timeout=timeout,
            kwargs={"row_factory": dict_row, "autocommit": False},
            open=True,
        )

    @contextmanager
    def transaction(self, user_id: UUID, role: str = "member") -> Iterator[Connection]:
        with self.pool.connection() as conn:
            with conn.transaction():
                if self.force_runtime_role:
                    conn.execute("SET LOCAL ROLE app_runtime")
                conn.execute("SET LOCAL statement_timeout = '5s'")
                conn.execute("SET LOCAL app.current_user_id = %s", (str(user_id),))
                conn.execute("SET LOCAL app.current_user_role = %s", (role,))
                yield conn

    def create_profile(self, user_id: UUID, profile_id: UUID, payload: dict) -> dict:
        birth = payload["birth"]
        with self.transaction(user_id) as conn:
            row = conn.execute(
                """INSERT INTO profiles
                   (id, owner_id, display_name_ciphertext, timezone, calendar_type,
                    birth_date_ciphertext, birth_time_ciphertext, birth_time_precision,
                    birth_location_ciphertext, latitude_ciphertext, longitude_ciphertext,
                    consent_version)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id, owner_id, created_at, updated_at""",
                (
                    profile_id, user_id, payload["display_name"].encode(), birth["timezone_id"],
                    birth["calendar_type"], birth["local_date"].encode(),
                    (birth.get("local_time") or "").encode(), birth["time_precision"],
                    json.dumps(birth["place"]).encode(), str(birth["place"]["latitude"]).encode(),
                    str(birth["place"]["longitude"]).encode(), payload["consent_version"],
                ),
            ).fetchone()
            return dict(row)

    def claim_idempotency(self, user_id: UUID, record_id: UUID, method: str, route: str,
                          key: str, fingerprint: str) -> str:
        """Atomically return claimed, replay, or conflict without logging request content."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        with self.transaction(user_id) as conn:
            inserted = conn.execute(
                """INSERT INTO idempotency_records
                   (id,owner_id,http_method,route_template,key_hash,request_fingerprint,state,
                    created_at,expires_at)
                   VALUES(%s,%s,%s,%s,%s,%s,'processing',now(),now()+interval '24 hours')
                   ON CONFLICT(owner_id,http_method,route_template,key_hash) DO NOTHING
                   RETURNING id""",
                (record_id, user_id, method, route, key_hash, fingerprint),
            ).fetchone()
            if inserted:
                return "claimed"
            existing = conn.execute(
                """SELECT request_fingerprint,state FROM idempotency_records
                   WHERE owner_id=%s AND http_method=%s AND route_template=%s AND key_hash=%s
                     AND expires_at > now()""",
                (user_id, method, route, key_hash),
            ).fetchone()
            if existing is None:
                return "expired"
            return "replay" if existing["request_fingerprint"] == fingerprint else "conflict"

    def close(self) -> None:
        self.pool.close()
