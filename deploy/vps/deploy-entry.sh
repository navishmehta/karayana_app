#!/usr/bin/env bash
# The ONLY thing GitHub Actions' deploy key may run on the server. Installed (root-owned, not editable by the
# kirana user) as /usr/local/bin/kirana-deploy and forced in ~kirana/.ssh/authorized_keys:
#   command="/usr/local/bin/kirana-deploy",restrict ssh-ed25519 AAAA... github-actions-deploy
#
# Accepts exactly "deploy <40-character commit sha>"; the website build (.tar.gz) arrives on stdin.
# The commit must already be on GitHub's main branch, so only code pushed to main can ever be deployed.
set -euo pipefail

read -r action sha extra <<<"${SSH_ORIGINAL_COMMAND:-}"
if [[ "$action" != deploy || ! "$sha" =~ ^[0-9a-f]{40}$ || -n "${extra:-}" ]]; then
  echo "Refused: expected 'deploy <commit sha>'." >&2
  exit 2
fi

cd /var/www/kirana/app
exec 9>/var/www/kirana/.deploy.lock
flock -w 900 9 || { echo "Another deploy is still running." >&2; exit 1; }

git fetch --quiet origin main
if ! git merge-base --is-ancestor "$sha" origin/main; then
  echo "Refused: $sha is not on main." >&2
  exit 2
fi
# A newer commit is already live (runs finished out of order): nothing to do.
if [ "$(git rev-parse HEAD)" != "$sha" ] && git merge-base --is-ancestor "$sha" HEAD; then
  echo "A newer version is already live — skipping $sha."
  cat >/dev/null
  exit 0
fi

git reset --quiet --hard "$sha"
exec deploy/vps/deploy.sh --web
