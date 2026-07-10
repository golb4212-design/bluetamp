#!/usr/bin/env python3
"""BlueTamp node latency service.

Provides HTTPS/CORS endpoint on port 2087. It accepts only a subscription token,
fetches that token's /raw payload from the same panel hostname as the browser
Origin, extracts public node endpoints, and measures TCP connect latency.
No raw config is returned to the browser.
"""
from __future__ import annotations

import base64
import concurrent.futures
import json
import os
import re
import socket
import ssl
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

PORT = int(os.getenv("BT_PORT", "2087"))
HOST = os.getenv("BT_HOST", "0.0.0.0")
CERTFILE = os.getenv("BT_SSL_CERTFILE", "").strip()
KEYFILE = os.getenv("BT_SSL_KEYFILE", "").strip()
INSECURE_PANEL_TLS = os.getenv("BT_INSECURE_PANEL_TLS", "0") == "1"
CACHE_TTL = max(15, int(os.getenv("BT_CACHE_TTL", "45")))
PING_TIMEOUT = max(0.5, float(os.getenv("BT_PING_TIMEOUT", "2.5")))
MAX_NODES = min(60, max(1, int(os.getenv("BT_MAX_NODES", "36"))))
TOKEN_RE = re.compile(r"^[A-Za-z0-9._~\-]{6,512}$")
PATH_RE = re.compile(r"^/[A-Za-z0-9._~\-/]{1,128}$")

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_LOCK = threading.Lock()
_RATE: dict[str, list[float]] = {}
_RATE_LOCK = threading.Lock()

COUNTRIES = [
    ("DE", "آلمان", r"(?:🇩🇪|\bde\b|germany|deutschland|آلمان)"),
    ("FI", "فنلاند", r"(?:🇫🇮|\bfi\b|finland|فنلاند)"),
    ("NL", "هلند", r"(?:🇳🇱|\bnl\b|netherlands|holland|هلند)"),
    ("FR", "فرانسه", r"(?:🇫🇷|\bfr\b|france|فرانسه)"),
    ("GB", "انگلیس", r"(?:🇬🇧|\buk\b|\bgb\b|united kingdom|england|britain|انگلیس)"),
    ("US", "آمریکا", r"(?:🇺🇸|\bus\b|\busa\b|united states|america|آمریکا)"),
    ("CA", "کانادا", r"(?:🇨🇦|\bca\b|canada|کانادا)"),
    ("TR", "ترکیه", r"(?:🇹🇷|\btr\b|turkey|turkiye|ترکیه)"),
    ("AE", "امارات", r"(?:🇦🇪|\bae\b|uae|emirates|dubai|امارات)"),
    ("SE", "سوئد", r"(?:🇸🇪|\bse\b|sweden|سوئد)"),
    ("CH", "سوئیس", r"(?:🇨🇭|\bch\b|switzerland|swiss|سوئیس)"),
    ("IT", "ایتالیا", r"(?:🇮🇹|\bit\b|italy|italia|ایتالیا)"),
    ("PL", "لهستان", r"(?:🇵🇱|\bpl\b|poland|لهستان)"),
    ("AT", "اتریش", r"(?:🇦🇹|\bat\b|austria|اتریش)"),
    ("ES", "اسپانیا", r"(?:🇪🇸|\bes\b|spain|espana|اسپانیا)"),
    ("BE", "بلژیک", r"(?:🇧🇪|\bbe\b|belgium|بلژیک)"),
    ("DK", "دانمارک", r"(?:🇩🇰|\bdk\b|denmark|دانمارک)"),
    ("NO", "نروژ", r"(?:🇳🇴|\bno\b|norway|نروژ)"),
    ("IE", "ایرلند", r"(?:🇮🇪|\bie\b|ireland|ایرلند)"),
    ("RO", "رومانی", r"(?:🇷🇴|\bro\b|romania|رومانی)"),
    ("BG", "بلغارستان", r"(?:🇧🇬|\bbg\b|bulgaria|بلغارستان)"),
    ("CZ", "چک", r"(?:🇨🇿|\bcz\b|czech|چک)"),
    ("HU", "مجارستان", r"(?:🇭🇺|\bhu\b|hungary|مجارستان)"),
    ("GR", "یونان", r"(?:🇬🇷|\bgr\b|greece|یونان)"),
    ("PT", "پرتغال", r"(?:🇵🇹|\bpt\b|portugal|پرتغال)"),
    ("RU", "روسیه", r"(?:🇷🇺|\bru\b|russia|روسیه)"),
    ("UA", "اوکراین", r"(?:🇺🇦|\bua\b|ukraine|اوکراین)"),
    ("AM", "ارمنستان", r"(?:🇦🇲|\bam\b|armenia|ارمنستان)"),
    ("GE", "گرجستان", r"(?:🇬🇪|\bge\b|georgia|گرجستان)"),
    ("AL", "آلبانی", r"(?:🇦🇱|\bal\b|albania|آلبانی)"),
    ("RS", "صربستان", r"(?:🇷🇸|\brs\b|serbia|صربستان)"),
    ("BA", "بوسنی", r"(?:🇧🇦|\bba\b|bosnia|بوسنی)"),
    ("EE", "استونی", r"(?:🇪🇪|\bee\b|estonia|استونی)"),
    ("LT", "لیتوانی", r"(?:🇱🇹|\blt\b|lithuania|لیتوانی)"),
    ("LV", "لتونی", r"(?:🇱🇻|\blv\b|latvia|لتونی)"),
    ("JP", "ژاپن", r"(?:🇯🇵|\bjp\b|japan|ژاپن)"),
    ("SG", "سنگاپور", r"(?:🇸🇬|\bsg\b|singapore|سنگاپور)"),
    ("IN", "هند", r"(?:🇮🇳|\bin\b|india|هند)"),
    ("BH", "بحرین", r"(?:🇧🇭|\bbh\b|bahrain|بحرین)"),
    ("MT", "مالت", r"(?:🇲🇹|\bmt\b|malta|مالت)"),
    ("TN", "تونس", r"(?:🇹🇳|\btn\b|tunisia|تونس)"),
]
COUNTRY_PATTERNS = [(code, name, re.compile(pattern, re.I)) for code, name, pattern in COUNTRIES]


def flag(code: str) -> str:
    if len(code) != 2:
        return "🌐"
    return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)


def country(text: str) -> tuple[str, str, str]:
    for code, name, pattern in COUNTRY_PATTERNS:
        if pattern.search(text):
            return code, name, flag(code)
    match = re.search(r"[\U0001F1E6-\U0001F1FF]{2}", text)
    return "", "لوکیشن", match.group(0) if match else "🌐"


def decode_b64(value: str) -> str:
    try:
        value = value.replace("-", "+").replace("_", "/").strip()
        value += "=" * (-len(value) % 4)
        return base64.b64decode(value).decode("utf-8", "replace")
    except Exception:
        return ""


def title_for(link: str, index: int) -> str:
    if link.lower().startswith("vmess://"):
        try:
            obj = json.loads(decode_b64(link[8:]))
            if obj.get("ps"):
                return str(obj["ps"])
        except Exception:
            pass
    try:
        parsed = urllib.parse.urlsplit(link)
        if parsed.fragment:
            return urllib.parse.unquote(parsed.fragment.replace("+", " "))
        query = urllib.parse.parse_qs(parsed.query)
        for key in ("name", "remark", "remarks", "tag"):
            if query.get(key):
                return urllib.parse.unquote(query[key][0])
    except Exception:
        pass
    return f"Node {index + 1}"


def protocol(link: str) -> str:
    low = link.lower()
    if low.startswith("vless://"):
        return "VLESS"
    if low.startswith("vmess://"):
        return "VMESS"
    if low.startswith("trojan://"):
        return "TROJAN"
    if low.startswith("ss://") or low.startswith("shadowsocks://"):
        return "SS"
    if low.startswith("hysteria"):
        return "HY2"
    return "VPN"


def parse_endpoint(link: str, index: int) -> dict[str, Any] | None:
    link = str(link or "").strip()
    if not link or link.lower().startswith("wireguard://") or link.lower().startswith("[interface]"):
        return None
    name = title_for(link, index)
    proto = protocol(link)
    host = ""
    port = 0
    try:
        if link.lower().startswith("vmess://"):
            obj = json.loads(decode_b64(link[8:]))
            host = str(obj.get("add") or obj.get("host") or "").strip()
            port = int(obj.get("port") or 443)
        elif link.lower().startswith("ss://"):
            body = link[5:].split("#", 1)[0].split("?", 1)[0]
            decoded = body if "@" in body else decode_b64(body)
            endpoint = decoded.rsplit("@", 1)[-1]
            if endpoint.startswith("["):
                end = endpoint.find("]")
                host = endpoint[1:end]
                port = int(endpoint[end + 2 :])
            else:
                host, port_text = endpoint.rsplit(":", 1)
                port = int(port_text)
        else:
            parsed = urllib.parse.urlsplit(link)
            host = parsed.hostname or ""
            port = parsed.port or (443 if parsed.scheme in {"vless", "vmess", "trojan", "hysteria", "hysteria2", "hy2"} else 0)
    except Exception:
        return None
    if not host or not (1 <= port <= 65535):
        return None
    code, cname, cflag = country(f"{name} {host}")
    return {
        "key": f"{host.lower()}:{port}",
        "host": host,
        "port": port,
        "title": name,
        "protocol": proto,
        "country_code": code,
        "country": cname,
        "flag": cflag,
    }


def extract_links(payload: Any, depth: int = 0) -> list[str]:
    if depth > 6 or payload is None:
        return []
    if isinstance(payload, str):
        raw = payload.strip()
        if not raw:
            return []
        try:
            return extract_links(json.loads(raw), depth + 1)
        except Exception:
            return [line.strip() for line in raw.splitlines() if "://" in line]
    if isinstance(payload, list):
        if all(isinstance(item, str) for item in payload):
            return [str(item).strip() for item in payload if str(item).strip()]
        output: list[str] = []
        for item in payload:
            output.extend(extract_links(item, depth + 1))
        return output
    if isinstance(payload, dict):
        for key in ("links", "configs", "proxies", "raw"):
            if key in payload:
                found = extract_links(payload[key], depth + 1)
                if found:
                    return found
        for key in ("body", "data", "result"):
            if key in payload:
                found = extract_links(payload[key], depth + 1)
                if found:
                    return found
    return []


def ping_node(node: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    online = False
    error = ""
    try:
        with socket.create_connection((node["host"], int(node["port"])), timeout=PING_TIMEOUT):
            online = True
    except Exception as exc:
        error = exc.__class__.__name__
    elapsed = round((time.perf_counter() - started) * 1000)
    result = dict(node)
    result.update({"online": online, "ping": elapsed if online else None})
    if error:
        result["error"] = error
    return result


def fetch_nodes(origin: str, token: str, sub_path: str) -> dict[str, Any]:
    key = f"{origin}|{sub_path}|{token}"
    now = time.time()
    with _CACHE_LOCK:
        cached = _CACHE.get(key)
        if cached and now - cached[0] < CACHE_TTL:
            return cached[1]

    raw_url = origin.rstrip("/") + sub_path.rstrip("/") + "/" + urllib.parse.quote(token, safe="") + "/raw"
    context = None
    if raw_url.startswith("https://") and INSECURE_PANEL_TLS:
        context = ssl._create_unverified_context()  # Explicit opt-in only.
    request = urllib.request.Request(raw_url, headers={"Accept": "application/json, text/plain, */*", "User-Agent": "BlueTamp-Nodes/1.0"})
    with urllib.request.urlopen(request, timeout=12, context=context) as response:
        body = response.read(4 * 1024 * 1024)
        content_type = response.headers.get("content-type", "")
    text = body.decode("utf-8", "replace")
    if "json" in content_type.lower():
        payload = json.loads(text)
    else:
        try:
            payload = json.loads(text)
        except Exception:
            payload = text
    links = extract_links(payload)
    seen: set[str] = set()
    nodes: list[dict[str, Any]] = []
    for idx, link in enumerate(links):
        node = parse_endpoint(link, idx)
        if not node or node["key"] in seen:
            continue
        seen.add(node["key"])
        nodes.append(node)
        if len(nodes) >= MAX_NODES:
            break
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(16, max(1, len(nodes)))) as pool:
        measured = list(pool.map(ping_node, nodes)) if nodes else []
    result = {"nodes": measured, "measured_at": int(time.time()), "count": len(measured)}
    with _CACHE_LOCK:
        _CACHE[key] = (now, result)
        if len(_CACHE) > 256:
            oldest = sorted(_CACHE.items(), key=lambda item: item[1][0])[:64]
            for old_key, _ in oldest:
                _CACHE.pop(old_key, None)
    return result


def allowed_request(client_ip: str) -> bool:
    now = time.time()
    with _RATE_LOCK:
        events = [stamp for stamp in _RATE.get(client_ip, []) if now - stamp < 60]
        if len(events) >= 30:
            _RATE[client_ip] = events
            return False
        events.append(now)
        _RATE[client_ip] = events
    return True


class Handler(BaseHTTPRequestHandler):
    server_version = "BlueTampNodes/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def origin(self) -> str:
        return (self.headers.get("Origin") or "").rstrip("/")

    def cors_origin(self) -> str:
        origin = self.origin()
        try:
            o = urllib.parse.urlsplit(origin)
            h = (self.headers.get("Host") or "").split(":", 1)[0].lower().strip("[]")
            if o.scheme in {"http", "https"} and o.hostname and o.hostname.lower() == h:
                return origin
        except Exception:
            pass
        return ""

    def common_headers(self, status: int = 200, content_type: str = "application/json; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        allowed = self.cors_origin()
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
            self.send_header("Vary", "Origin")
        self.end_headers()

    def json_response(self, payload: Any, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        allowed = self.cors_origin()
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        allowed = self.cors_origin()
        if not allowed:
            self.json_response({"error": "origin_not_allowed"}, 403)
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", allowed)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Accept, Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/health":
            self.json_response({"ok": True, "tls": bool(CERTFILE and KEYFILE), "port": PORT})
            return
        if parsed.path != "/nodes":
            self.json_response({"error": "not_found"}, 404)
            return
        if not allowed_request(self.client_address[0]):
            self.json_response({"error": "rate_limited"}, 429)
            return
        origin = self.cors_origin()
        if not origin:
            self.json_response({"error": "origin_not_allowed"}, 403)
            return
        query = urllib.parse.parse_qs(parsed.query)
        token = (query.get("token") or [""])[0]
        sub_path = (query.get("sub_path") or ["/sub"])[0]
        if not TOKEN_RE.fullmatch(token):
            self.json_response({"error": "invalid_token"}, 400)
            return
        if not PATH_RE.fullmatch(sub_path) or ".." in sub_path:
            self.json_response({"error": "invalid_path"}, 400)
            return
        try:
            result = fetch_nodes(origin, token, sub_path)
            self.json_response(result)
        except urllib.error.HTTPError as exc:
            self.json_response({"error": "panel_http_error", "status": exc.code}, 502)
        except Exception as exc:
            self.json_response({"error": "node_probe_failed", "detail": exc.__class__.__name__}, 502)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    if CERTFILE and KEYFILE and os.path.isfile(CERTFILE) and os.path.isfile(KEYFILE):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(CERTFILE, KEYFILE)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        scheme = "https"
    else:
        scheme = "http"
    print(f"BlueTamp node service listening on {scheme}://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
