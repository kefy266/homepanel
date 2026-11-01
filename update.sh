#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo "Lütfen sudo ile çalıştır: sudo bash update.sh"; exit 1; fi
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="/opt/homepanel"
install -d -o homepanel -g homepanel "$APP_DIR"
cp -a "$SCRIPT_DIR/backend" "$SCRIPT_DIR/frontend" "$SCRIPT_DIR/requirements.txt" "$APP_DIR/"
chown -R homepanel:homepanel "$APP_DIR"
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
systemctl restart homepanel
echo "HomePanel güncellendi."
