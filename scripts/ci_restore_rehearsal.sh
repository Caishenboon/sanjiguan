#!/usr/bin/env bash
set -euo pipefail

restore_container="sanji-v1-restore-${GITHUB_RUN_ID:-local}"
restore_volume="${restore_container}-data"
dump_file="${RUNNER_TEMP:-/tmp}/sanji-v1-restore.dump"
demo_file="${RUNNER_TEMP:-/tmp}/sanji-v1-demo.json"

cleanup() {
  docker rm -f "$restore_container" >/dev/null 2>&1 || true
  docker volume rm "$restore_volume" >/dev/null 2>&1 || true
  rm -f "$dump_file" "$demo_file"
}
trap cleanup EXIT

set -a
# shellcheck disable=SC1091
source .env
set +a

python scripts/demo.py create > "$demo_file"
python - "$demo_file" <<'PY'
import json, sys
data=json.load(open(sys.argv[1], encoding="utf-8"))
assert data["synthetic"] is True
assert data["liuxiang_replay_matched"] is True
assert data["life_trend_replay_matched"] is True
assert data["narrative_source"] == "deterministic_template"
assert data["core_output_hash"].startswith("sha256:")
PY

docker compose exec -T postgres \
  pg_dump -U migration_owner -d "$POSTGRES_DB" -Fc > "$dump_file"
test -s "$dump_file"

# Destroy the source database and its volume before creating the restore target.
docker compose down --volumes
docker volume create "$restore_volume" >/dev/null
docker run -d --name "$restore_container" \
  -e POSTGRES_USER=migration_owner \
  -e POSTGRES_PASSWORD="$POSTGRES_MIGRATION_PASSWORD" \
  -e POSTGRES_DB="$POSTGRES_DB" \
  -v "$restore_volume:/var/lib/postgresql/data" \
  postgres:16.10-bookworm >/dev/null

stable_checks=0
for attempt in $(seq 1 30); do
  if docker exec "$restore_container" pg_isready -U migration_owner -d "$POSTGRES_DB" >/dev/null 2>&1; then
    stable_checks=$((stable_checks + 1))
    if [ "$stable_checks" -ge 3 ]; then
      break
    fi
  else
    stable_checks=0
  fi
  sleep 1
done
test "$stable_checks" -ge 3
docker exec "$restore_container" pg_isready -U migration_owner -d "$POSTGRES_DB"
docker exec "$restore_container" psql -U migration_owner -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c \
  "CREATE ROLE app_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;"
docker exec -i "$restore_container" \
  pg_restore -U migration_owner -d "$POSTGRES_DB" --no-owner --no-acl < "$dump_file"

profile_id="$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["profile_id"])' "$demo_file")"
expected_hash="$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["core_output_hash"])' "$demo_file")"
actual_hash="$(docker exec "$restore_container" psql -U migration_owner -d "$POSTGRES_DB" -Atc \
  "SELECT core_output_hash FROM life_trend_executions WHERE profile_id='${profile_id}' ORDER BY created_at LIMIT 1")"
test "$actual_hash" = "$expected_hash"

docker exec "$restore_container" psql -U migration_owner -d "$POSTGRES_DB" -Atc \
  "SELECT count(*) > 0 FROM sanji_archive_entries WHERE profile_id='${profile_id}'" | grep '^t$'
docker exec "$restore_container" psql -U migration_owner -d "$POSTGRES_DB" -Atc \
  "SELECT count(*) FROM schema_migrations" | grep -E '^[1-9][0-9]*$'
echo "Synthetic backup/restore rehearsal passed with stable archive hash."
