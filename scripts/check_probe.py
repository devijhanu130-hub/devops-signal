"""Execute inside a demo pod; verify readiness failure without liveness failure."""
import urllib.error
import urllib.request

with urllib.request.urlopen("http://localhost:8080/healthz", timeout=5) as response:
    assert response.status == 200
try:
    urllib.request.urlopen("http://localhost:8080/readyz", timeout=5)
except urllib.error.HTTPError as error:
    assert error.code == 503, error.code
else:
    raise AssertionError("Expected readiness HTTP 503")
print("Readiness returned 503 while liveness stayed healthy.")
