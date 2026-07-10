#!/usr/bin/env bash
set -euo pipefail
REPO="golb4212-design/bluetamp"
BRANCH="main"
TARGET_DIR="/var/lib/pasarguard/templates/subscription"
TARGET_FILE="$TARGET_DIR/index.html"
ENV_FILE="/opt/pasarguard/.env"
SERVICE_DIR="/opt/bluetamp-nodes"
SERVICE_ENV="/etc/bluetamp-nodes.env"
RAW="https://raw.githubusercontent.com/$REPO/$BRANCH"

if [[ $EUID -ne 0 ]]; then echo "این اسکریپت را با sudo اجرا کنید."; exit 1; fi
command -v curl >/dev/null || { echo "curl نصب نیست."; exit 1; }
command -v python3 >/dev/null || { echo "python3 نصب نیست."; exit 1; }

mkdir -p "$TARGET_DIR" "$SERVICE_DIR"
[[ -f "$TARGET_FILE" ]] && cp -a "$TARGET_FILE" "$TARGET_FILE.backup.$(date +%Y%m%d-%H%M%S)"

curl -4 -fL --connect-timeout 20 --retry 3 -H "Cache-Control: no-cache" "$RAW/index.html?v=7" -o "$TARGET_FILE.tmp"
grep -q "BlueTamp PasarGuard Subscription Template v7.0.0" "$TARGET_FILE.tmp" || { echo "فایل index.html نسخه ۷ نیست. ابتدا فایل‌های جدید را در GitHub جایگزین کنید."; rm -f "$TARGET_FILE.tmp"; exit 1; }
mv "$TARGET_FILE.tmp" "$TARGET_FILE"
chmod 0644 "$TARGET_FILE"

curl -4 -fL --connect-timeout 20 --retry 3 -H "Cache-Control: no-cache" "$RAW/bluetamp_nodes.py?v=7" -o "$SERVICE_DIR/bluetamp_nodes.py"
curl -4 -fL --connect-timeout 20 --retry 3 -H "Cache-Control: no-cache" "$RAW/bluetamp-nodes.service?v=7" -o /etc/systemd/system/bluetamp-nodes.service
chmod 0755 "$SERVICE_DIR/bluetamp_nodes.py"
chmod 0644 /etc/systemd/system/bluetamp-nodes.service

read_env() {
  local key="$1"
  [[ -f "$ENV_FILE" ]] || return 0
  sed -nE "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*['\"]?([^'\"#]+)['\"]?[[:space:]]*$/\1/p" "$ENV_FILE" | tail -n1 | xargs
}
CERT="$(read_env UVICORN_SSL_CERTFILE || true)"
KEY="$(read_env UVICORN_SSL_KEYFILE || true)"
cat > "$SERVICE_ENV" <<EOF
BT_HOST=0.0.0.0
BT_PORT=2087
BT_CACHE_TTL=45
BT_PING_TIMEOUT=2.5
BT_MAX_NODES=36
BT_INSECURE_PANEL_TLS=0
BT_SSL_CERTFILE=$CERT
BT_SSL_KEYFILE=$KEY
EOF
chmod 0600 "$SERVICE_ENV"

if [[ -f "$ENV_FILE" ]]; then
  sed -i '/^CUSTOM_TEMPLATES_DIRECTORY=/d;/^SUBSCRIPTION_PAGE_TEMPLATE=/d' "$ENV_FILE"
  printf '\nCUSTOM_TEMPLATES_DIRECTORY="/var/lib/pasarguard/templates/"\nSUBSCRIPTION_PAGE_TEMPLATE="subscription/index.html"\n' >> "$ENV_FILE"
else
  echo "هشدار: $ENV_FILE پیدا نشد و تنظیمات قالب باید دستی وارد شود."
fi

systemctl daemon-reload
systemctl enable --now bluetamp-nodes.service

if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q '^Status: active'; then
  ufw allow 2087/tcp comment 'BlueTamp node latency' >/dev/null || true
fi

pasarguard restart
sleep 2

if [[ -n "$CERT" && -n "$KEY" && -f "$CERT" && -f "$KEY" ]]; then
  curl -ksS --connect-timeout 5 https://127.0.0.1:2087/health >/dev/null && echo "سرویس پینگ HTTPS فعال شد: پورت 2087"
else
  echo "هشدار: مسیر گواهی TLS پاسارگارد پیدا نشد. سرویس روی HTTP:2087 اجرا شد."
  echo "برای صفحه HTTPS باید همان گواهی دامنه را در /etc/bluetamp-nodes.env وارد کنید و سرویس را ری‌استارت کنید."
fi

echo "BlueTamp v7 و سرویس گره‌ها نصب شد."
