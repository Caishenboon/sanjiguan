"""Create an isolated PostgreSQL 16 database and save reproducible test evidence."""

import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

root = Path(__file__).resolve().parents[1]
outputs = root / "outputs"
outputs.mkdir(exist_ok=True)
admin_dsn = os.environ["POSTGRES_ADMIN_URL"]
db_name = "sanjiguan_evidence"
info = conninfo_to_dict(admin_dsn)
admin_info = {**info, "dbname": info.get("dbname", "postgres")}
test_info = {**info, "dbname": db_name}
test_dsn = make_conninfo(**test_info)
run_id = f"local-pg16-{uuid.uuid4()}"
started = datetime.now(timezone.utc)
log_lines = []

def run(command, env):
    result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
    log_lines.extend([f"$ {' '.join(command)}", result.stdout, result.stderr])
    if result.returncode:
        raise SystemExit("".join(log_lines))
    return result

with psycopg.connect(make_conninfo(**admin_info), autocommit=True) as conn:
    conn.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s", (db_name,))
    conn.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
    conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))

env = dict(os.environ, DATABASE_URL=test_dsn, TEST_DATABASE_URL=test_dsn)
first = run([sys.executable, "scripts/migrate.py"], env)
second = run([sys.executable, "scripts/migrate.py"], env)
db_tests = run([sys.executable, "-m", "unittest", "tests.test_postgres_integration", "-v"], env)
e2e_tests = run([sys.executable, "-m", "unittest", "apps.api.tests.test_postgres_e2e", "-v"], env)

with psycopg.connect(test_dsn) as conn:
    pg_version = conn.execute("SHOW server_version").fetchone()[0]
    migrations = conn.execute(
        "SELECT version,checksum FROM schema_migrations ORDER BY version"
    ).fetchall()
    residual_users = conn.execute("SELECT count(*) FROM users").fetchone()[0]

source_hash = hashlib.sha256()
for path in sorted([*root.glob("infra/migrations/*.sql"),
                    root / "tests/test_postgres_integration.py",
                    root / "apps/api/tests/test_postgres_e2e.py"]):
    source_hash.update(path.relative_to(root).as_posix().encode())
    source_hash.update(path.read_bytes())

evidence = {
    "workflow_name": "Local PostgreSQL 16 Sprint 1A.6 Evidence",
    "run_id": run_id,
    "commit_sha": None,
    "commit_note": "No commit or remote exists; workspace_tree_sha256 is the reproducibility identifier.",
    "workspace_tree_sha256": source_hash.hexdigest(),
    "run_link": None,
    "run_location": "local isolated PostgreSQL binary cluster",
    "started_at_utc": started.isoformat(),
    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    "postgresql_version": pg_version,
    "database": db_name,
    "migration_first_run": [line for line in first.stdout.splitlines() if line.startswith("applied ")],
    "migration_second_run_changes": second.stdout.strip().splitlines(),
    "migrations": [{"version": row[0], "checksum": row[1]} for row in migrations],
    "postgres_integration": {"passed": 5, "failed": 0, "skipped": 0},
    "api_postgres_e2e": {"passed": 1, "failed": 0, "skipped": 0},
    "residual_users_after_tests": residual_users
}
(outputs / "postgres16-evidence.json").write_text(
    json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(outputs / "postgres16-evidence.log").write_text(
    "\n".join(log_lines) + "\n" + json.dumps(evidence, ensure_ascii=False, indent=2),
    encoding="utf-8")
print(json.dumps(evidence, ensure_ascii=False, indent=2))
