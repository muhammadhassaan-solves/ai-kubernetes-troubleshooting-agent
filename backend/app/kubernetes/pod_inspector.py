import json
from typing import Any

from app.kubernetes.kubectl import KubectlExecutor, KubectlResult

UNHEALTHY_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "Pending",
    "Error",
    "OOMKilled",
    "ContainerCreating",
}


class PodInspector:
    def __init__(self, kubectl: KubectlExecutor) -> None:
        self.kubectl = kubectl

    def inspect(self) -> dict[str, Any]:
        result = self.kubectl.run(["get", "pods", "-A", "-o", "json"])
        if not result.success:
            return self._failure(result)

        payload = json.loads(result.stdout or "{}")
        pods = payload.get("items", [])
        problematic_pods = []

        for pod in pods:
            issue = self._detect_pod_issue(pod)
            if issue:
                metadata = pod.get("metadata", {})
                problematic_pods.append(
                    {
                        "name": metadata.get("name", ""),
                        "namespace": metadata.get("namespace", "default"),
                        "status": issue["status"],
                        "message": issue["message"],
                    }
                )

        return {
            "healthy": len(problematic_pods) == 0,
            "total_pods": len(pods),
            "problematic_pods": problematic_pods,
        }

    def _detect_pod_issue(self, pod: dict[str, Any]) -> dict[str, Any] | None:
        status = pod.get("status", {})
        phase = status.get("phase", "")

        container_statuses = status.get("containerStatuses", [])
        init_container_statuses = status.get("initContainerStatuses", [])

        for container in init_container_statuses + container_statuses:
            container_name = container.get("name", "")
            state = container.get("state", {})
            waiting = state.get("waiting")
            terminated = state.get("terminated")
            last_terminated = container.get("lastState", {}).get("terminated")

            if waiting:
                reason = waiting.get("reason", "")
                if reason in UNHEALTHY_REASONS:
                    return {
                        "status": reason,
                        "container": container_name,
                        "message": waiting.get("message", ""),
                    }

            if terminated:
                reason = terminated.get("reason", "Error")
                if reason in UNHEALTHY_REASONS or terminated.get("exitCode", 0) != 0:
                    return {
                        "status": reason,
                        "container": container_name,
                        "exit_code": terminated.get("exitCode", 0),
                        "message": terminated.get("message", ""),
                    }

            if last_terminated and last_terminated.get("reason") == "OOMKilled":
                return {
                    "status": "OOMKilled",
                    "container": container_name,
                    "exit_code": last_terminated.get("exitCode", 137),
                    "message": last_terminated.get("message", ""),
                }

        if phase in {"Pending", "Failed", "Unknown"}:
            return {"status": phase, "message": status.get("message", "")}

        return None

    def _failure(self, result: KubectlResult) -> dict[str, Any]:
        return {
            "healthy": False,
            "total_pods": 0,
            "problematic_pods": [],
            "error": result.stderr.strip(),
        }
