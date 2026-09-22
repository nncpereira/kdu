#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATE=$(date +%Y-%m-%d_%H%M%S)
RETENTION_DAYS="${RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"

echo "==> Backing up database…"
docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc \
    > "$BACKUP_DIR/db_${DATE}.dump"

echo "==> Backing up media (receipts, attachments)…"
docker run --rm \
    -v kdu_media_files:/media:ro \
    -v "$(pwd)/$BACKUP_DIR":/backup \
    alpine tar czf "/backup/media_${DATE}.tar.gz" -C /media .

echo "==> Removing backups older than ${RETENTION_DAYS} days…"
find "$BACKUP_DIR" -name "*.dump" -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +"$RETENTION_DAYS" -delete

echo "==> Backup complete: $BACKUP_DIR/db_${DATE}.dump"
echo "    Backup complete: $BACKUP_DIR/media_${DATE}.tar.gz"

# Optional: copy to external storage
# rsync -avz "$BACKUP_DIR/" user@backup-server:/backups/kdu/