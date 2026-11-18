#!/usr/bin/env bash
# Nightly backup: database every day, product images on Sundays, 30 days kept.
# Optional off-site copy with rclone when RCLONE_REMOTE is set in .env.
set -euo pipefail
cd "$(dirname "$0")"
set -a
# shellcheck source=/dev/null  # exists only on the server
. ./.env
set +a

KEEP_DAYS=30
STAMP=$(date -u +%Y-%m-%d_%H%M)
mkdir -p backups

docker compose exec -T db sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers kirana' \
  | gzip > "backups/db_${STAMP}.sql.gz"
echo "Database backup: backups/db_${STAMP}.sql.gz"

if [ "$(date -u +%u)" = "7" ]; then
  docker compose run --rm --no-deps -v "$(pwd)/backups:/backups" --entrypoint sh api \
    -c "tar -czf /backups/media_${STAMP}.tar.gz -C /data media" && echo "Images backup: backups/media_${STAMP}.tar.gz"
fi

find backups -type f -mtime +"$KEEP_DAYS" -delete

if [ -n "${RCLONE_REMOTE:-}" ] && command -v rclone >/dev/null; then
  rclone copy backups "$RCLONE_REMOTE" --max-age 2d && echo "Copied to $RCLONE_REMOTE"
fi
