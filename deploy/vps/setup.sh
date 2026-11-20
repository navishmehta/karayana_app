#!/usr/bin/env bash
# ONE-TIME setup of Smart Kirana on the shared Hostinger VPS (run as root). Adds only Kirana's own things:
# user "kirana", /var/www/kirana, /etc/kirana/env, MySQL database + user "kirana", kirana-backend.service,
# one nginx site. It does not touch other sites, databases or services. Safe to run again.
#
#   bash setup.sh            (copy this file to the server first; it clones the repo itself)
set -euo pipefail

REPO=https://github.com/navishmehta/karayana_app.git
DOMAIN=kirana.thecodemate.com
BASE=/var/www/kirana
UV_VERSION=0.13.9

[ "$(id -u)" = 0 ] || { echo "Run as root."; exit 1; }

echo "==> User and folders"
id kirana >/dev/null 2>&1 || useradd --system --home-dir "$BASE" --create-home --shell /bin/bash kirana
install -d -o kirana -g kirana -m 711 "$BASE"                      # nginx may pass through, not list
install -d -o kirana -g kirana -m 755 "$BASE/web" "$BASE/web/releases" "$BASE/media"
install -d -o kirana -g kirana -m 700 "$BASE/backups" "$BASE/logs" "$BASE/.ssh"
install -d -o root -g kirana -m 750 /etc/kirana

echo "==> Code"
[ -d "$BASE/app/.git" ] || sudo -u kirana git clone --quiet "$REPO" "$BASE/app"
chmod 750 "$BASE/app"

echo "==> uv (Python package manager, for the kirana user only)"
[ -x "$BASE/.local/bin/uv" ] || sudo -iu kirana bash -c \
  "curl -LsSf https://astral.sh/uv/$UV_VERSION/install.sh | env UV_NO_MODIFY_PATH=1 sh -s -- --quiet"

echo "==> Database (new database + user, only access to that database)"
if [ ! -f /etc/kirana/env ]; then
  DB_PASSWORD="$(openssl rand -hex 24)"
  mysql -e "CREATE DATABASE IF NOT EXISTS kirana CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER IF NOT EXISTS 'kirana'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
    CREATE USER IF NOT EXISTS 'kirana'@'127.0.0.1' IDENTIFIED BY '$DB_PASSWORD';
    ALTER USER 'kirana'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
    ALTER USER 'kirana'@'127.0.0.1' IDENTIFIED BY '$DB_PASSWORD';
    GRANT ALL PRIVILEGES ON kirana.* TO 'kirana'@'localhost';
    GRANT ALL PRIVILEGES ON kirana.* TO 'kirana'@'127.0.0.1';"

  ADMIN_PASSWORD="$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-14)Aa1!"
  echo "==> Writing /etc/kirana/env"
  umask 027
  cat >/etc/kirana/env <<EOF
# Smart Kirana live settings. Secrets — never commit. Read by kirana-backend.service and deploy scripts.
ENVIRONMENT=production
DEBUG=false
DB_PASSWORD=$DB_PASSWORD
DATABASE_URL=mysql+pymysql://kirana:$DB_PASSWORD@127.0.0.1:3306/kirana

STORE_TIMEZONE=Asia/Kolkata
STORE_CURRENCY=INR
DEFAULT_STORE_NAME="Ramesh Karayana Store"

ADMIN_NAME="Store Admin"
ADMIN_EMAIL=admin@thecodemate.com
ADMIN_PASSWORD=$ADMIN_PASSWORD

JWT_SECRET=$(openssl rand -hex 32)
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=30

MAIL_DRIVER=smtp
MAIL_FROM_ADDRESS=support@thecodemate.com
MAIL_FROM_NAME="Ramesh Karayana Store"
SMTP_HOST=smtp.hostinger.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=support@thecodemate.com
SMTP_PASSWORD=

PUSH_DRIVER=expo
EXPO_PUSH_ACCESS_TOKEN=

MEDIA_DRIVER=local
MEDIA_ROOT=$BASE/media
MEDIA_BASE_URL=https://$DOMAIN/media
CORS_ORIGINS=[]
EOF
  chown root:kirana /etc/kirana/env
  chmod 640 /etc/kirana/env
  echo
  echo "    Admin login: admin@thecodemate.com / $ADMIN_PASSWORD   (save it; change it in the app later)"
  echo
fi

echo "==> Deploy command (root-owned) and the restart permission it needs"
install -o root -g root -m 755 "$BASE/app/deploy/vps/deploy-entry.sh" /usr/local/bin/kirana-deploy
cat >/etc/sudoers.d/kirana <<'EOF'
kirana ALL=(root) NOPASSWD: /usr/bin/systemctl restart kirana-backend, /usr/bin/journalctl -u kirana-backend -n 40 --no-pager
EOF
chmod 440 /etc/sudoers.d/kirana
visudo -cf /etc/sudoers.d/kirana >/dev/null

echo "==> API service"
install -o root -g root -m 644 "$BASE/app/deploy/vps/kirana-backend.service" /etc/systemd/system/kirana-backend.service
systemctl daemon-reload
systemctl enable kirana-backend >/dev/null

echo "==> nginx site (tested before reload; other sites untouched)"
if [ ! -f /etc/nginx/sites-available/$DOMAIN ]; then
  install -o root -g root -m 644 "$BASE/app/deploy/vps/nginx.conf" /etc/nginx/sites-available/$DOMAIN
  ln -s /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/$DOMAIN
  if ! nginx -t 2>/dev/null; then
    rm -f /etc/nginx/sites-enabled/$DOMAIN
    echo "nginx config test failed — removed the new site again, nothing reloaded."; nginx -t; exit 1
  fi
  systemctl reload nginx
fi

echo "==> Scheduled jobs"
sudo -u kirana crontab "$BASE/app/deploy/vps/crontab"

echo "==> Setup done. Next: first deploy (sudo -iu kirana bash -c 'cd app && deploy/vps/deploy.sh'), then HTTPS:"
echo "    certbot --nginx -d $DOMAIN --redirect --non-interactive"
