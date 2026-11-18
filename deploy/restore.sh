#!/usr/bin/env bash
# Restore the database from a backup:  ./restore.sh backups/db_2026-11-20_2100.sql.gz
# Test this regularly on a copy — a backup is only useful if it can be restored.
set -euo pipefail
cd "$(dirname "$0")"
FILE=${1:?usage: ./restore.sh backups/db_<date>.sql.gz}
[ -f "$FILE" ] || { echo "No such file: $FILE"; exit 1; }

read -r -p "This REPLACES all current data with $FILE. Type RESTORE to continue: " answer
[ "$answer" = "RESTORE" ] || { echo "Cancelled."; exit 1; }

docker compose stop api
gunzip -c "$FILE" | docker compose exec -T db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" kirana'
docker compose start api
echo "Restored from $FILE"
