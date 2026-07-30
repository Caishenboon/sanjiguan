"""Create a PostgreSQL custom-format backup plus a checksummed manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
dsn = os.environ["BACKUP_DATABASE_URL"]
args.output.mkdir(parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
dump = args.output / f"sanjiguan-{stamp}.dump"
subprocess.run(
    ["pg_dump", "--format=custom", "--no-owner", "--no-acl", "--file", str(dump), dsn],
    check=True,
)
digest = hashlib.sha256(dump.read_bytes()).hexdigest()
manifest = {
    "schema_version": "sanji-backup/1.0",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "application_version": os.getenv("SANJI_VERSION", "unknown"),
    "migration_version": os.getenv("SANJI_MIGRATION_VERSION", "inspect-on-restore"),
    "database_dump": dump.name,
    "sha256": digest,
    "encryption": "external_required_for_off-host_storage",
}
(args.output / f"sanjiguan-{stamp}.manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(dump)
