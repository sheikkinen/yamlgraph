"""FR-784 SPA fixture server — dynamic handler shared by tests and smokes.

Single source of truth for the `_SpaHandler` semantics frozen by FR-784
(one data fetch, one telemetry fetch, one token-bearing fetch, an auth
wall, a CAPTCHA page, a hanging request). Imported by
tests/unit/test_fr784_network_sniff.py and runnable standalone so live
authoring smokes (FR-809 AC-05/AC-06) can serve the committed fixture:

    python tests/fixtures/fr784_spa/spa_server.py --port 8799
"""

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent


class SpaHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str, **headers):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in headers.items():
            self.send_header(key.replace("_", "-"), value)
        self.end_headers()
        self.wfile.write(body)

    def _route(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html", "/auth.html", "/captcha.html", "/hang.html"):
            name = "index.html" if path == "/" else path.lstrip("/")
            body = (FIXTURE_DIR / name).read_bytes()
            self._send(200, body, "text/html")
        elif path == "/api/data":
            body = json.dumps({"items": [{"id": 1, "name": "fixture-row"}]}).encode()
            self._send(200, body, "application/json")
        elif path == "/api/item":
            self._send(200, json.dumps({"id": 1}).encode(), "application/json")
        elif path == "/api/search":
            self._send(200, json.dumps({"hits": []}).encode(), "application/json")
        elif path == "/analytics/collect":
            self._send(204, b"", "text/plain")
        elif path == "/api/secure":
            self._send(
                401,
                json.dumps({"error": "unauthorized"}).encode(),
                "application/json",
                WWW_Authenticate="Bearer",
            )
        elif path == "/hang":
            time.sleep(120)  # never answers within any test timeout
        else:
            self._send(404, b"not found", "text/plain")

    do_GET = _route
    do_POST = _route

    def log_message(self, fmt, *args):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the FR-784 SPA fixture")
    parser.add_argument("--port", type=int, default=8799)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), SpaHandler)
    server.daemon_threads = True
    print(f"serving FR-784 SPA fixture at http://127.0.0.1:{args.port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
