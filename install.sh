#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo "Lütfen sudo ile çalıştır: sudo bash install.sh"; exit 1; fi
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="/opt/homepanel"
SERVICE_USER="homepanel"
ENV_FILE="/etc/homepanel.env"
echo "[HomePanel] Bağımlılıklar kuruluyor..."
apt-get update
apt-get install -y python3 python3-venv python3-pip
if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" "$APP_DIR" /srv/homepanel/uploads
cp -a "$SCRIPT_DIR/backend" "$SCRIPT_DIR/frontend" "$SCRIPT_DIR/requirements.txt" "$APP_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR" /srv/homepanel
if [[ ! -f "$ENV_FILE" ]]; then
  ADMIN_PASSWORD="$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)"
  FLASK_SECRET="$(openssl rand -hex 32)"
  printf 'ADMIN_PASSWORD=%s\nFLASK_SECRET=%s\nUPLOAD_DIR=/srv/homepanel/uploads\nPORT=8787\n' "$ADMIN_PASSWORD" "$FLASK_SECRET" > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo
  echo "HomePanel yönetici şifren (şimdi kaydet): $ADMIN_PASSWORD"
else
  echo "Mevcut $ENV_FILE korundu."
fi
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
cat > /etc/systemd/system/homepanel.service <<'UNIT'
[Unit]
Description=HomePanel self-hosted dashboard
After=network.target

[Service]
Type=simple
User=homepanel
Group=homepanel
WorkingDirectory=/opt/homepanel
EnvironmentFile=/etc/homepanel.env
ExecStart=/opt/homepanel/.venv/bin/python /opt/homepanel/backend/app.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/srv/homepanel/uploads
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
LockPersonality=true
RestrictSUIDSGID=true
RestrictRealtime=true
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now homepanel
echo
echo "[HomePanel] Kurulum tamamlandı."
echo "Panel: http://SUNUCU-IP:8787"
echo "Servis durumu: sudo systemctl status homepanel"
