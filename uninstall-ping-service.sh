#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo "با sudo اجرا کنید."; exit 1; fi
systemctl disable --now bluetamp-nodes.service 2>/dev/null || true
rm -f /etc/systemd/system/bluetamp-nodes.service /etc/bluetamp-nodes.env
rm -rf /opt/bluetamp-nodes
systemctl daemon-reload
if command -v ufw >/dev/null 2>&1; then ufw delete allow 2087/tcp >/dev/null 2>&1 || true; fi
echo "سرویس پینگ BlueTamp حذف شد؛ قالب اشتراک دست‌نخورده باقی ماند."
