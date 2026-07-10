#!/usr/bin/env bash
set -euo pipefail

REPO="golb4212-design/bluetamp"
BRANCH="main"
TARGET_DIR="/var/lib/pasarguard/templates/subscription"
TARGET_FILE="$TARGET_DIR/index.html"
ENV_FILE="/opt/pasarguard/.env"
URL="https://raw.githubusercontent.com/$REPO/$BRANCH/index.html?v=4"

if [[ $EUID -ne 0 ]]; then
  echo "این اسکریپت را با sudo اجرا کنید."
  exit 1
fi

mkdir -p "$TARGET_DIR"
if [[ -f "$TARGET_FILE" ]]; then
  cp -a "$TARGET_FILE" "$TARGET_FILE.backup.$(date +%Y%m%d-%H%M%S)"
fi

curl -4 -fL --connect-timeout 20 --retry 3 -H "Cache-Control: no-cache" "$URL" -o "$TARGET_FILE.tmp"
grep -q "BlueTamp PasarGuard Subscription Template v4.0.0" "$TARGET_FILE.tmp" || {
  echo "فایل دانلودشده نسخه ۴ نیست. ابتدا index.html جدید را در GitHub جایگزین کنید."
  rm -f "$TARGET_FILE.tmp"
  exit 1
}
mv "$TARGET_FILE.tmp" "$TARGET_FILE"
chmod 0644 "$TARGET_FILE"

if [[ -f "$ENV_FILE" ]]; then
  sed -i '/^CUSTOM_TEMPLATES_DIRECTORY=/d;/^SUBSCRIPTION_PAGE_TEMPLATE=/d' "$ENV_FILE"
  printf '\nCUSTOM_TEMPLATES_DIRECTORY="/var/lib/pasarguard/templates/"\nSUBSCRIPTION_PAGE_TEMPLATE="subscription/index.html"\n' >> "$ENV_FILE"
else
  echo "هشدار: فایل $ENV_FILE پیدا نشد. تنظیمات قالب را دستی وارد کنید."
fi

pasarguard restart

echo "BlueTamp v4 نصب شد."
