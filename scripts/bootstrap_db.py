"""Apply migrations and provision the restricted runtime role password."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import psycopg
from psycopg import sql


root = Path(__file__).resolve().parents[1]
dsn = os.environ["MIGRATION_DATABASE_URL"]
runtime_password = os.environ["POSTGRES_APP_PASSWORD"]
if len(runtime_password) < 24 or runtime_password.lower() in {"change-me", "password", "default"}:
    raise SystemExit("POSTGRES_APP_PASSWORD must be a generated value of at least 24 characters")

with psycopg.connect(dsn, autocommit=True) as conn:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
        version text PRIMARY KEY, checksum text NOT NULL,
        applied_at timestamptz NOT NULL DEFAULT now())"""
    )
    for path in sorted((root / "infra/migrations").glob("*.sql")):
        migration_sql = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(migration_sql.encode()).hexdigest()
        prior = conn.execute(
            "SELECT checksum FROM schema_migrations WHERE version=%s", (path.name,)
        ).fetchone()
        if prior:
            if prior[0] != checksum:
                raise SystemExit(f"migration drift: {path.name}")
            continue
        conn.execute(migration_sql)
        conn.execute(
            "INSERT INTO schema_migrations(version,checksum) VALUES (%s,%s)",
            (path.name, checksum),
        )
        print(f"applied {path.name}")
    conn.execute(
        sql.SQL("ALTER ROLE app_runtime PASSWORD {}").format(sql.Literal(runtime_password))
    )
    role = conn.execute(
        """SELECT rolname,rolsuper,rolcreatedb,rolcreaterole,rolbypassrls
           FROM pg_roles WHERE rolname='app_runtime'"""
    ).fetchone()
    if not role or any(role[1:]):
        raise SystemExit("app_runtime privilege invariant failed")
print("database ready; app_runtime remains non-owner and NOBYPASSRLS")
