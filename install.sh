#!/usr/bin/env bash
set -Eeuo pipefail

RAW_URL="https://raw.githubusercontent.com/golb4212-design/bluetamp/main/index.html"
TEMPLATE_DIR="/var/lib/pasarguard/templates/subscription"
TEMPLATE_FILE="${TEMPLATE_DIR}/index.html"
ENV_FILE="/opt/pasarguard/.env"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "این اسکریپت باید با sudo یا کاربر root اجرا شود."
  exit 1
fi

for command in wget grep sed cp mkdir; do
  command -v "${command}" >/dev/null 2>&1 || {
    echo "دستور موردنیاز پیدا نشد: ${command}"
    exit 1
  }
done

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "فایل تنظیمات پاسارگارد پیدا نشد: ${ENV_FILE}"
  exit 1
fi

mkdir -p "${TEMPLATE_DIR}"

if [[ -f "${TEMPLATE_FILE}" ]]; then
  cp -a "${TEMPLATE_FILE}" "${TEMPLATE_FILE}.backup-${STAMP}"
fi
cp -a "${ENV_FILE}" "${ENV_FILE}.backup-${STAMP}"

TEMP_FILE="$(mktemp)"
trap 'rm -f "${TEMP_FILE}"' EXIT
wget -q --https-only --timeout=20 --tries=3 -O "${TEMP_FILE}" "${RAW_URL}"

if ! grep -q '<!doctype html>' "${TEMP_FILE}"; then
  echo "فایل دانلودشده معتبر نیست؛ نصب متوقف شد."
  exit 1
fi

install -m 0644 "${TEMP_FILE}" "${TEMPLATE_FILE}"

set_env_value() {
  local key="$1"
  local value="$2"
  if grep -qE "^[[:space:]]*${key}=" "${ENV_FILE}"; then
    sed -i -E "s|^[[:space:]]*${key}=.*$|${key}=\"${value}\"|" "${ENV_FILE}"
  else
    printf '\n%s="%s"\n' "${key}" "${value}" >> "${ENV_FILE}"
  fi
}

set_env_value "CUSTOM_TEMPLATES_DIRECTORY" "/var/lib/pasarguard/templates/"
set_env_value "SUBSCRIPTION_PAGE_TEMPLATE" "subscription/index.html"

if command -v pasarguard >/dev/null 2>&1; then
  pasarguard restart
  echo "قالب BlueTamp نصب و پاسارگارد ری‌استارت شد."
else
  echo "قالب نصب شد، اما دستور pasarguard پیدا نشد. سرویس را دستی ری‌استارت کنید."
fi
