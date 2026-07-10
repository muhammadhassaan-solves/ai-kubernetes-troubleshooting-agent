import json
from typing import Any

from app.kubernetes.kubectl import KubectlExecutor, KubectlResult


class DeploymentInspector:
    def __init__(self, kubectl: KubectlExecutor) -> None:
        self.kubectl = kubectl

    def inspect(self) -> dict[str, Any]:
        result = self.kubectl.run(["get", "deployments", "-A", "-o", "json"])
        if not result.success:
            return self._failure(result)

        payload = json.loads(result.stdout or "{}")
        deployments = payload.get("items", [])
        unhealthy_deployments = []

        for deployment in deployments:
            issue = self._detect_deployment_issue(deployment)
            if issue:
                metadata = deployment.get("metadata", {})
                unhealthy_deployments.append(
                    {
                        "name": metadata.get("name", ""),
                        "namespace": metadata.get("namespace", "default"),
                        **issue,
                    }
                )

        return {
            "healthy": len(unhealthy_deployments) == 0,
            "total_deployments": len(deployments),
            "unhealthy_deployments": unhealthy_deployments,
        }

    def _detect_deployment_issue(self, deployment: dict[str, Any]) -> dict[str, Any] | None:
        spec = deployment.get("spec", {})
        status = deployment.get("status", {})
        desired = spec.get("replicas", 1)
        available = status.get("availableReplicas", 0)
        unavailable = status.get("unavailableReplicas", 0)
        updated = status.get("updatedReplicas", 0)
        conditions = status.get("conditions", [])
        condition_issues = []

        for condition in conditions:
            condition_type = condition.get("type", "")
            condition_status = condition.get("status", "")
            if (
                condition_type == "Available"
                and condition_status != "True"
                or condition_type == "Progressing"
                and condition_status == "False"
            ):
                condition_issues.append(
                    {
                        "type": condition_type,
                        "status": condition_status,
                        "reason": condition.get("reason", ""),
                        "message": condition.get("message", ""),
                    }
                )

        if unavailable > 0 or available < desired or condition_issues:
            return {
                "desired_replicas": desired,
                "available_replicas": available,
                "unavailable_replicas": unavailable,
                "updated_replicas": updated,
                "conditions": condition_issues,
            }

        return None

    def _failure(self, result: KubectlResult) -> dict[str, Any]:
        return {
            "healthy": False,
            "total_deployments": 0,
            "unhealthy_deployments": [],
            "error": result.stderr.strip(),
        }

