"""DevOps Signal: a small, dependency-free infrastructure learning service."""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

STARTED = time.monotonic()
COUNTS = {200: 0, 404: 0, 503: 0}
COUNTS_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "DevOpsSignal/1.0"
    sys_version = ""

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self.reply(200, b"DevOps Signal\nA personal project for container delivery and observability.\nEndpoints: /healthz /readyz /api/info /metrics\n", "text/plain; charset=utf-8")
        elif path == "/healthz":
            self.json_reply({"status": "ok", "check": "liveness"})
        elif path == "/readyz":
            ready = os.getenv("APP_READY", "true").lower() == "true"
            self.json_reply({"status": "ok" if ready else "not_ready", "check": "readiness"}, 200 if ready else 503)
        elif path == "/api/info":
            self.json_reply({"service": "devops-signal", "version": os.getenv("APP_VERSION", "dev"), "environment": os.getenv("APP_ENV", "local")})
        elif path == "/metrics":
            with COUNTS_LOCK:
                counts = dict(COUNTS)
            lines = ["# HELP signal_requests_total Handled GET requests by HTTP status.", "# TYPE signal_requests_total counter"]
            lines.extend(f'signal_requests_total{{status="{status}"}} {count}' for status, count in sorted(counts.items()))
            lines.extend(["# HELP signal_uptime_seconds Process age in seconds.", "# TYPE signal_uptime_seconds gauge", f"signal_uptime_seconds {time.monotonic() - STARTED:.3f}"])
            self.reply(200, ("\n".join(lines) + "\n").encode(), "text/plain; version=0.0.4; charset=utf-8")
        else:
            self.reply(404, b'{"error":"not_found"}\n', "application/json")

    def json_reply(self, data, status=200):
        self.reply(status, (json.dumps(data) + "\n").encode(), "application/json")

    def reply(self, status, body, content_type):
        with COUNTS_LOCK:
            COUNTS[status] += 1
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(json.dumps({"event": "http_request", "message": format % args}), flush=True)


def make_server(host="0.0.0.0", port=8080):
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    server = make_server(port=int(os.getenv("PORT", "8080")))
    print(json.dumps({"event": "server_started", "port": server.server_port}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
