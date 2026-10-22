import concurrent.futures
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from app import make_server


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server("127.0.0.1", 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def get(self, path):
        return urllib.request.urlopen(self.base + path, timeout=5)

    def test_health_and_readiness_are_separate_checks(self):
        for path, check in [("/healthz", "liveness"), ("/readyz", "readiness")]:
            with self.subTest(path=path), self.get(path) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(json.load(response), {"status": "ok", "check": check})

    def test_info_uses_deployment_configuration(self):
        with patch.dict(os.environ, {"APP_VERSION": "test-sha", "APP_ENV": "test"}), self.get("/api/info") as response:
            body = json.load(response)
            self.assertEqual(body["version"], "test-sha")
            self.assertEqual(body["environment"], "test")
            self.assertNotIn("PATH", body)

    def test_unknown_route_returns_json_404(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.get("/does-not-exist")
        self.assertEqual(caught.exception.code, 404)
        self.assertEqual(json.load(caught.exception), {"error": "not_found"})

    def test_metrics_count_completed_requests_and_include_uptime(self):
        with self.get("/metrics") as response:
            before = response.read().decode()
        count = lambda text: int(next(line.split()[-1] for line in text.splitlines() if line.startswith('signal_requests_total{status="200"}')))
        with self.get("/healthz") as response:
            response.read()
        with self.get("/metrics") as response:
            after = response.read().decode()
        self.assertGreaterEqual(count(after), count(before) + 2)
        self.assertIn("# TYPE signal_requests_total counter", after)
        self.assertIn("signal_uptime_seconds", after)

    def test_concurrent_requests_complete(self):
        def fetch(_):
            with self.get("/readyz") as response:
                return response.status
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(fetch, range(12))), [200] * 12)

    def test_response_headers_and_query_string(self):
        with self.get("/healthz?probe=1") as response:
            body = response.read()
            self.assertEqual(int(response.headers["Content-Length"]), len(body))
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(response.headers["Cache-Control"], "no-store")


if __name__ == "__main__":
    unittest.main()
