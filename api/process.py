import json
import os
import traceback
from http.server import BaseHTTPRequestHandler

# Vercel เขียนไฟล์ได้เฉพาะ /tmp
os.environ.setdefault("PYTHAINLP_DATA", "/tmp/pythainlp-data")

engine, LOAD_ERROR = None, None
try:
    try:
        from .engine import ChatLertEngine
    except ImportError:
        from engine import ChatLertEngine
    engine = ChatLertEngine()
except Exception:
    LOAD_ERROR = traceback.format_exc()
    print(LOAD_ERROR, flush=True)  # เห็นเฉพาะใน Vercel Logs


class handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if LOAD_ERROR:
            return self._send(500, {"ok": False, "error": "engine failed to load"})
        self._send(200, {"ok": True, "service": "chatlert"})

    def do_POST(self):
        if LOAD_ERROR:
            return self._send(500, {"error": "engine failed to load"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, {"error": "invalid json"})
        text = str(body.get("text", "")).strip()[:500]
        if not text:
            return self._send(400, {"error": "empty"})
        try:
            self._send(200, engine.process(text))
        except Exception:
            print(traceback.format_exc(), flush=True)
            self._send(500, {"error": "internal error"})
