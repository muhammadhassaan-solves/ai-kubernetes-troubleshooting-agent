# Kubernetes Failure Testing

Use these manifests to validate the full troubleshooting flow against real
cluster failures.

## Apply Scenarios

```bash
kubectl apply -f k8s-test-scenarios/
```

Then open the dashboard, select the same kubeconfig context, and click
`Investigate Cluster`.

## Expected Failures

| Scenario | Expected signal | Expected diagnosis |
| --- | --- | --- |
| CrashLoopBackOff | `missing-env-crashloop` exits on startup | Missing environment variable |
| ImagePullBackOff | `bad-image-tag` uses a non-existent image tag | Invalid image or tag |
| OOMKilled | `oom-killed-demo` exceeds memory limit | Container exceeded memory limit |
| Service selector mismatch | `selector-mismatch-service` has no ready endpoints | Service selector does not match pod labels |

## Cleanup

```bash
kubectl delete namespace ai-kubernetes-agent-test
```

If a scenario does not appear immediately, wait for Kubernetes to update pod
status and events:

```bash
kubectl get pods -n ai-kubernetes-agent-test
kubectl get events -n ai-kubernetes-agent-test --sort-by=.lastTimestamp
```

