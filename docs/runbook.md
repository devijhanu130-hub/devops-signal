# Readiness failure: operational runbook

This is an exercise for the local `kind-signal` demo cluster. It is not a record of a production incident.

## Symptoms

Pods are running but not ready; rollout is waiting; requests through the Service may fail because it has no ready endpoints.

## Inspect before changing anything

```sh
kubectl --context kind-signal get pods -l app=devops-signal
kubectl --context kind-signal describe deployment devops-signal
kubectl --context kind-signal logs -l app=devops-signal --tail=50
kubectl --context kind-signal get endpointslices -l kubernetes.io/service-name=devops-signal
```

## Inject a controlled readiness failure

Start with a healthy local deployment. The app's `APP_READY` flag is an explicit simulation control, not a dependency health check.

```sh
kubectl --context kind-signal set env deployment/devops-signal APP_READY=false
kubectl --context kind-signal get pods -l app=devops-signal
```

Expected behavior: newly created pods return 503 from `/readyz` while `/healthz` still returns 200. With `maxUnavailable: 0`, existing healthy pods can continue serving while rollout waits. This demonstrates why a dependency-style readiness failure should not cause a liveness restart loop. Do not claim zero downtime from these settings alone; inspect actual events and responses.

## Recover

```sh
kubectl --context kind-signal set env deployment/devops-signal APP_READY=true
kubectl --context kind-signal rollout status deployment/devops-signal --timeout=120s
kubectl --context kind-signal port-forward service/devops-signal 8080:80
```

Then request `/readyz` and confirm 200. Record elapsed recovery time only after running the experiment; do not use invented MTTR or availability metrics.

## Roll back an unintended configuration change

```sh
kubectl --context kind-signal rollout history deployment/devops-signal
kubectl --context kind-signal rollout undo deployment/devops-signal
kubectl --context kind-signal rollout status deployment/devops-signal --timeout=120s
```

Check the target context before any command. The rollback restores a previous pod-template revision, not external data or deleted resources.
