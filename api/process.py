import json
from http.server import BaseHTTPRequestHandler

try:
    from .engine import ChatLertEngine
except ImportError:
    from engine import ChatLertEngine

engine = ChatLertEngine()


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
        # เปิด /api/process ในเบราว์เซอร์เพื่อเช็กว่า API ทำงานอยู่
        self._send(200, {"ok": True, "service": "chatlert"})

    def do_POST(self):
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
        except Exception as e:
            self._send(500, {"error": str(e)})
