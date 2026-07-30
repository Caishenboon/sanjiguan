"""Restore a verified custom-format backup into an empty target database."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

import psycopg


parser = argparse.ArgumentParser()
parser.add_argument("manifest", type=Path)
args = parser.parse_args()
manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
dump = args.manifest.parent / manifest["database_dump"]
if hashlib.sha256(dump.read_bytes()).hexdigest() != manifest["sha256"]:
    raise SystemExit("backup checksum mismatch")
dsn = os.environ["RESTORE_DATABASE_URL"]
with psycopg.connect(dsn) as conn:
    count = conn.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
    ).fetchone()[0]
    if count:
        raise SystemExit("restore target must be empty")
subprocess.run(
    ["pg_restore", "--no-owner", "--no-acl", "--exit-on-error", "--dbname", dsn, str(dump)],
    check=True,
)
with psycopg.connect(dsn) as conn:
    migrations = conn.execute("SELECT count(*) FROM schema_migrations").fetchone()[0]
    archives = conn.execute("SELECT count(*) FROM sanji_archive_entries").fetchone()[0]
    hashes = conn.execute(
        """SELECT count(*) FROM sanji_archive_entries
           WHERE output_hash ~ '^sha256:[a-f0-9]{64}$'"""
    ).fetchone()[0]
    if migrations < 19 or archives != hashes:
        raise SystemExit("restored database invariant failed")
print(json.dumps({"status": "restored", "migrations": migrations, "archive_hashes": hashes}))
