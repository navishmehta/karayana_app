#!/usr/bin/env bash
# Install or update Smart Kirana on the server:  ./deploy.sh
# Safe to run again: database migrations and starter data only add what is missing.
set -euo pipefail
cd "$(dirname "$0")"

[ -f .env ] || { echo "Missing deploy/.env — copy .env.example and fill it in."; exit 1; }

echo "==> Getting the latest code"
git -C .. pull --ff-only

echo "==> Building images"
docker compose build

echo "==> Starting the database"
docker compose up -d db
until [ "$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose ps -q db)")" = "healthy" ]; do sleep 2; done

echo "==> Backing up before changing the database"
./backup.sh || echo "(backup skipped — first install?)"

echo "==> Updating the database structure"
docker compose run --rm api alembic upgrade head

echo "==> Starting the API and the website"
docker compose up -d

echo "==> Adding starter data if missing (store, roles, admin, units, settings, categories)"
docker compose exec -T api python -m app.cli seed

docker image prune -f >/dev/null
echo "==> Done. Check: https://$(grep '^DOMAIN=' .env | cut -d= -f2)/api/v1/health"
