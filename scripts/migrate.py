"""Apply ordered SQL migrations and record checksums."""

import hashlib
import os
from pathlib import Path

import psycopg

root = Path(__file__).resolve().parents[1]
dsn = os.environ["DATABASE_URL"]
files = sorted((root / "infra/migrations").glob("*.sql"))

with psycopg.connect(dsn, autocommit=True) as conn:
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
        version text PRIMARY KEY, checksum text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now()
    )""")
    for path in files:
        sql = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql.encode()).hexdigest()
        prior = conn.execute(
            "SELECT checksum FROM schema_migrations WHERE version=%s", (path.name,)
        ).fetchone()
        if prior:
            if prior[0] != checksum:
                raise SystemExit(f"migration drift: {path.name}")
            continue
        conn.execute(sql)
        conn.execute(
            "INSERT INTO schema_migrations(version,checksum) VALUES (%s,%s)",
            (path.name, checksum),
        )
        print(f"applied {path.name}")
