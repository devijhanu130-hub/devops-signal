"""Select a running demo pod configured for the readiness experiment."""
import json
import sys

for pod in json.load(sys.stdin)["items"]:
    if pod["status"].get("phase") != "Running":
        continue
    env = {item["name"]: item.get("value") for item in pod["spec"]["containers"][0].get("env", [])}
    if env.get("APP_READY") == "false":
        print(pod["metadata"]["name"])
        break
