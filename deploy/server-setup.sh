#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu 24.04 server (as your normal user):  sudo bash server-setup.sh
set -euo pipefail

echo "==> Updating the system and enabling automatic security updates"
apt-get update -y
apt-get upgrade -y
apt-get install -y ca-certificates curl git ufw unattended-upgrades
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "==> Installing Docker (official repository)"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
# shellcheck source=/dev/null  # exists only on the server
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Let the user who ran "sudo" use docker without sudo (takes effect after logging in again)
if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then usermod -aG docker "$SUDO_USER"; fi

echo "==> Firewall: only SSH, HTTP and HTTPS"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw --force enable

echo "==> Done. Next: clone the repository to /opt/smart-kirana and follow docs/DEPLOYMENT.md"
