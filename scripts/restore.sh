#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup-file.dump>"
    exit 1
fi

DUMP_FILE="$1"

if [ ! -f "$DUMP_FILE" ]; then
    echo "Backup file not found: $DUMP_FILE"
    exit 1
fi

echo "==> WARNING: This will REPLACE the current database."
read -p "Type 'yes' to continue: " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo "==> Stopping backend…"
docker compose -f docker-compose.prod.yml stop backend

echo "==> Restoring database…"
docker compose -f docker-compose.prod.yml exec -T db \
    pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists \
    < "$DUMP_FILE"

echo "==> Starting backend…"
docker compose -f docker-compose.prod.yml start backend

echo "==> Restore complete."