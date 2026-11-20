#!/usr/bin/env bash
# Run a backend command with the live settings, e.g.:
#   deploy/vps/run.sh python -m app.cli refresh-stock
set -euo pipefail
cd /var/www/kirana/app/backend
set -a; . /etc/kirana/env; set +a
exec ".venv/bin/$1" "${@:2}"
