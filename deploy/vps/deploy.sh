#!/usr/bin/env bash
# Update Smart Kirana on the Hostinger VPS (kirana.thecodemate.com). Runs as the "kirana" user.
#
# Normally started by GitHub Actions on every push to main (through deploy/vps/deploy-entry.sh).
# By hand, on the server:   sudo -iu kirana bash -c 'cd app && git pull --ff-only && deploy/vps/deploy.sh'
#
#   --web   a .tar.gz of the website build (npx expo export --platform web) arrives on stdin
#
# Safe to run again: migrations and starter data only add what is missing.
set -euo pipefail

BASE=/var/www/kirana
APP="$BASE/app"
PORT=8030
export PATH="$BASE/.local/bin:$PATH"

set -a; . /etc/kirana/env; set +a
cd "$APP/backend"
echo "==> Deploying $(git -C "$APP" log -1 --format='%h %s')"

# 1. Unpack the website build first (stdin must be read now); it goes live only after the API is healthy.
NEW_WEB=""
if [ "${1:-}" = "--web" ]; then
  NEW_WEB="$BASE/web/releases/$(date -u +%Y%m%d%H%M%S)-$(git -C "$APP" rev-parse --short HEAD)"
  mkdir -p "$NEW_WEB"
  tar -xzf - -C "$NEW_WEB"
  [ -f "$NEW_WEB/index.html" ] || { echo "Website build has no index.html — stopping."; rm -rf "$NEW_WEB"; exit 1; }
fi

echo "==> Installing Python packages"
uv sync --frozen --no-dev --quiet

echo "==> Backing up the database"
"$APP/deploy/vps/backup.sh" pre-deploy

echo "==> Updating the database structure"
.venv/bin/alembic upgrade head

echo "==> Adding starter data if missing"
.venv/bin/python -m app.cli seed

echo "==> Restarting the API"
sudo -n /usr/bin/systemctl restart kirana-backend
for _ in $(seq 30); do
  curl -sf "http://127.0.0.1:$PORT/api/v1/health" >/dev/null && break
  sleep 1
done
if ! curl -sf "http://127.0.0.1:$PORT/api/v1/health" >/dev/null; then
  echo "!! The API did not come back. Last log lines:"
  sudo -n /usr/bin/journalctl -u kirana-backend -n 40 --no-pager || true
  [ -n "$NEW_WEB" ] && rm -rf "$NEW_WEB"
  exit 1
fi

if [ -n "$NEW_WEB" ]; then
  echo "==> Publishing the website"
  ln -sfn "$NEW_WEB" "$BASE/web/current.tmp"
  mv -T "$BASE/web/current.tmp" "$BASE/web/current"
  # Keep the last 5 website builds (for a quick manual rollback).
  ls -1dt "$BASE"/web/releases/* | tail -n +6 | xargs -r rm -rf
fi

echo "==> Done: https://kirana.thecodemate.com/api/v1/health"
