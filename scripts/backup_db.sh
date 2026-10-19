#!/bin/sh
# Postgres backup for the local Docker stack (managed-provider snapshots take
# over on staging/prod). Usage: sh scripts/backup_db.sh [output_dir]
# Restores with: psql < backup file (see runbook in Docs/APP_WORKFLOW.md).
set -eu
OUT_DIR="${1:-backups}"
mkdir -p "$OUT_DIR"
STAMP=$(date +%Y%m%d-%H%M%S)
FILE="$OUT_DIR/watersphere-$STAMP.sql"
cd "$(dirname "$0")/.."
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-watersphere}" "${POSTGRES_DB:-watersphere}" > "$FILE"
echo "backup ok: $FILE ($(wc -c < "$FILE") bytes)"
