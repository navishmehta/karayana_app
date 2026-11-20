#!/usr/bin/env bash
# Database backup (daily at 02:30 IST and before every deploy) + product photos (Sundays). Keeps 30 days.
# Files: /var/www/kirana/backups/   Restore a database backup (as root):
#   gunzip -c /var/www/kirana/backups/db_<...>.sql.gz | mysql kirana
set -euo pipefail

BASE=/var/www/kirana
DIR="$BASE/backups"
KIND="${1:-daily}"   # daily | pre-deploy

set -a; . /etc/kirana/env; set +a
mkdir -p "$DIR"
umask 077
stamp="$(date -u +%Y-%m-%d_%H%M%S)"

out="$DIR/db_${KIND}_$stamp.sql.gz"
MYSQL_PWD="$DB_PASSWORD" mysqldump -u kirana -h 127.0.0.1 --single-transaction --no-tablespaces kirana | gzip >"$out.tmp"
mv "$out.tmp" "$out"
echo "Backup: $out"

if [ "$KIND" = daily ] && [ "$(date -u +%u)" = 7 ]; then
  tar -czf "$DIR/media_$stamp.tar.gz" -C "$BASE" media
  echo "Photos: $DIR/media_$stamp.tar.gz"
fi

find "$DIR" -name '*.gz' -mtime +30 -delete
