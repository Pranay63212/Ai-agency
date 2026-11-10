"""Small web server that receives customer replies.

    POST /sms/<client-slug>     Twilio "A message comes in" webhook (form fields From, Body)
    POST /email/<client-slug>   JSON {"from": "...", "body": "..."} from an email forwarder
    GET  /health                returns ok

If TWILIO_AUTH_TOKEN and PUBLIC_URL are set, Twilio's signature is checked on every /sms request,
so nobody else can post fake replies. Set PUBLIC_URL to the address Twilio calls, e.g.
https://your-app.example.com (no trailing slash). Email posts need ?key=WEBHOOK_KEY when it's set.
"""

import base64
import hashlib
import hmac
import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from xml.sax.saxutils import escape

from .campaign import Campaign
from .replies import handle_reply


def twilio_signature_ok(url: str, params: dict, signature: str, token: str) -> bool:
    data = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    expected = base64.b64encode(hmac.new(token.encode(), data.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(expected, signature or "")


def make_handler(root: str, provider: str | None, auto_reply: bool):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: str, ctype: str = "text/plain") -> None:
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _campaign(self, slug: str) -> Campaign | None:
            if not slug.replace("-", "").isalnum():
                return None
            c = Campaign(os.path.join(root, slug))
            return c if os.path.exists(c.settings_path) else None

        def do_GET(self):
            self._send(200, "ok") if self.path == "/health" else self._send(404, "not found")

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            parts = parsed.path.strip("/").split("/")
            if len(parts) != 2 or parts[0] not in {"sms", "email"}:
                return self._send(404, "not found")
            campaign = self._campaign(parts[1])
            if not campaign:
                return self._send(404, "unknown client")
            raw = self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 100_000)).decode()

            if parts[0] == "sms":
                params = {k: v[0] for k, v in urllib.parse.parse_qs(raw, keep_blank_values=True).items()}
                token, public = os.environ.get("TWILIO_AUTH_TOKEN"), os.environ.get("PUBLIC_URL")
                if token and public and not twilio_signature_ok(
                        public + self.path, params, self.headers.get("X-Twilio-Signature", ""), token):
                    return self._send(403, "bad signature")
                result = handle_reply(campaign, params.get("From", ""), params.get("Body", ""),
                                      provider, auto_reply)
                msg = f"<Message>{escape(result['send_back'])}</Message>" if result["send_back"] else ""
                return self._send(200, f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response>{msg}</Response>",
                                  "application/xml")

            key = os.environ.get("WEBHOOK_KEY")
            if key and urllib.parse.parse_qs(parsed.query).get("key", [""])[0] != key:
                return self._send(403, "bad key")
            try:
                payload = json.loads(raw or "{}")
            except json.JSONDecodeError:
                return self._send(400, "bad json")
            result = handle_reply(campaign, payload.get("from", ""), payload.get("body", ""), provider, False)
            return self._send(200, json.dumps(result), "application/json")

        def log_message(self, fmt, *args):
            print("[webhook]", fmt % args)

    return Handler


def serve(root: str, host: str, port: int, provider: str | None, auto_reply: bool) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(root, provider, auto_reply))
    print(f"Listening on http://{host}:{port}  (POST /sms/<client>, /email/<client>)")
    server.serve_forever()
