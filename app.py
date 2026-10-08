#!/usr/bin/env python3
"""Komodo Custom Alerter -> Telegram relay.

Komodo POSTs its Alert JSON here; we format it and call the Bot API.
Only reachable inside the komodo compose network, so there is no auth.
"""
import html
import json
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
CHAT_ID = os.environ["TG_CHAT_ID"]
THREAD_ID = os.environ.get("TG_THREAD_ID", "").strip()  # forum topic, optional
KOMODO_HOST = os.environ.get("KOMODO_HOST", "").rstrip("/")

ICON = {"OK": "✅", "WARNING": "⚠️", "CRITICAL": "🔴"}
SKIP = {"id", "err"}


def esc(v):
    return html.escape(str(v), quote=False)


def fmt(alert):
    level = alert.get("level", "?")
    resolved = alert.get("resolved", False)
    data = alert.get("data") or {}
    kind = data.get("type", "?")
    fields = data.get("data") or {}
    icon = "✅" if resolved else ICON.get(level, "ℹ️")
    head = f"{icon} <b>{esc(kind)}</b> {esc(level)}" + (" (resolved)" if resolved else "")
    lines = [head]
    name = fields.get("name")
    if name:
        lines.append(f"<b>{esc(name)}</b>")
    for k, v in fields.items():
        if k in SKIP or k == "name" or v is None or v == "":
            continue
        if isinstance(v, float):
            v = f"{v:.1f}"
        lines.append(f"{esc(k)}: <code>{esc(v)[:200]}</code>")
    err = fields.get("err")
    if err:
        msg = err.get("error") if isinstance(err, dict) else err
        lines.append(f"err: <code>{esc(msg)[:300]}</code>")
    target = alert.get("target") or {}
    if KOMODO_HOST and target.get("type") and target.get("id"):
        lines.append(f'{KOMODO_HOST}/{target["type"].lower()}s/{target["id"]}')
    return "\n".join(lines)


def send(text):
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML",
               "disable_web_page_preview": True}
    if THREAD_ID:
        payload["message_thread_id"] = int(THREAD_ID)
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n)
        try:
            alert = json.loads(raw or b"{}")
            text = fmt(alert)
        except Exception as e:  # malformed payload: still forward something
            text = f"⚠️ unparseable alert: <code>{esc(e)}</code>\n<code>{esc(raw[:500].decode(errors='replace'))}</code>"
        try:
            send(text)
        except Exception as e:
            print(f"telegram send failed: {e}", file=sys.stderr, flush=True)
            self.send_response(502)
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok\n")

    def log_message(self, fmt_, *args):
        print(f"{self.address_string()} {fmt_ % args}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), H).serve_forever()
