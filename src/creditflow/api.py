"""Read-only aggregate API; bind to localhost for the portfolio demo."""
import json
from importlib.resources import files
import sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler, HTTPServer


def make_server(database, host="127.0.0.1", port=8000):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                payload = files("creditflow").joinpath("dashboard.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            if self.path not in ("/health", "/v1/daily"):
                self.send_error(404)
                return
            try:
                with closing(sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True)) as con:
                    con.row_factory = sqlite3.Row
                    if self.path == "/health":
                        last = con.execute("SELECT started_at FROM runs ORDER BY rowid DESC LIMIT 1").fetchone()
                        body = {"status": "ok" if last else "not_ready", "last_success": last[0] if last else None}
                        status = 200 if last else 503
                    else:
                        body = [dict(r) for r in con.execute("SELECT * FROM gold_daily ORDER BY application_date, channel")]
                        status = 200
            except sqlite3.Error:
                body, status = {"status": "unavailable"}, 503
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
    return HTTPServer((host, port), Handler)

def serve(database, host="127.0.0.1", port=8000):
    with make_server(database, host, port) as server:
        server.serve_forever()
