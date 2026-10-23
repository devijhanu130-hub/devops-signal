# Verification record

## Dashboard increment — October 23, 2026

Eleven HTTP tests passed locally, including serving the dashboard. Browser checks against the running Python service verified healthy probes, readiness 503 with liveness 200, real counters and rates, disconnected-state metric clearing, and reconnection after restart. [Screenshots and reproduction steps](dashboard.md).

These checks verify the lightweight direct-metrics dashboard. They do not verify a live Prometheus scrape or Grafana. The workflow result below is historical and predates this increment.

## Original pipeline evidence

Date: October 22, 2026.

| Check | Status |
| --- | --- |
| Python HTTP tests | Ten tests passed locally and in GitHub Actions |
| Docker image build | Passed in GitHub Actions |
| Read-only, non-root container smoke test | Passed in GitHub Actions |
| Trivy vulnerability scan | Passed the configured gate for fixable HIGH and CRITICAL findings; this does not mean there are no vulnerabilities |
| Prometheus configuration and alert rules | Validated with promtool in GitHub Actions |
| Kubernetes deployment and HTTP probes | Passed in an ephemeral Kind cluster in GitHub Actions |
| Readiness failure and recovery | Verified HTTP 503 readiness alongside HTTP 200 liveness, then recovered the deployment |
| Live Prometheus scrape/dashboard | Not verified; Compose configuration is provided |
| GitHub Actions run | Both jobs passed: [execution evidence](https://github.com/devijhanu130-hub/devops-signal/actions/runs/39854092436) |

Verified code commit: `3630fab`. Docker and Kubernetes were executed on the GitHub-hosted runner, not on the preparation computer. The temporary cluster was deleted by the workflow. There is no persistent cloud deployment and no measured production uptime or business impact claim.
