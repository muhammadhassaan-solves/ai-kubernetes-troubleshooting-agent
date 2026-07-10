import json
from typing import Any

from app.kubernetes.kubectl import KubectlExecutor


class NetworkInspector:
    def __init__(self, kubectl: KubectlExecutor) -> None:
        self.kubectl = kubectl

    def inspect(self) -> dict[str, Any]:
        services_result = self.kubectl.run(["get", "svc", "-A", "-o", "json"])
        endpoints_result = self.kubectl.run(["get", "endpoints", "-A", "-o", "json"])
        pods_result = self.kubectl.run(["get", "pods", "-A", "-o", "json"])

        if not services_result.success:
            return {
                "healthy": False,
                "services_checked": 0,
                "issues": [],
                "error": services_result.stderr.strip(),
            }

        services = json.loads(services_result.stdout or "{}").get("items", [])
        endpoints = (
            json.loads(endpoints_result.stdout or "{}").get("items", [])
            if endpoints_result.success
            else []
        )
        pods = (
            json.loads(pods_result.stdout or "{}").get("items", [])
            if pods_result.success
            else []
        )

        endpoint_lookup = {
            (
                item.get("metadata", {}).get("namespace", "default"),
                item.get("metadata", {}).get("name", ""),
            ): item
            for item in endpoints
        }
        pods_by_namespace = self._group_pods_by_namespace(pods)

        issues = []
        warnings = []
        for service in services:
            metadata = service.get("metadata", {})
            spec = service.get("spec", {})
            namespace = metadata.get("namespace", "default")
            name = metadata.get("name", "")
            service_type = spec.get("type", "ClusterIP")
            selector = spec.get("selector", {})

            if service_type == "ExternalName":
                continue

            if not selector:
                warnings.append(
                    f"Service {namespace}/{name} has no selector; this can be intentional",
                )
                continue

            matching_pods = self._matching_pods(
                pods_by_namespace.get(namespace, []),
                selector,
            )
            endpoint = endpoint_lookup.get((namespace, name), {})
            has_endpoints = any(
                subset.get("addresses") for subset in endpoint.get("subsets", [])
            )

            if not matching_pods:
                issues.append(
                    {
                        "service": name,
                        "namespace": namespace,
                        "issue": "Selector does not match any pods",
                        "selector": selector,
                    }
                )
            elif not has_endpoints:
                issues.append(
                    {
                        "service": name,
                        "namespace": namespace,
                        "issue": "Service has no ready endpoints",
                        "selector": selector,
                    }
                )

        return {
            "healthy": len(issues) == 0,
            "services_checked": len(services),
            "issues": issues,
            "warnings": warnings
            + self._warnings(endpoints_result.success, pods_result.success),
        }

    def _group_pods_by_namespace(
        self,
        pods: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for pod in pods:
            namespace = pod.get("metadata", {}).get("namespace", "default")
            grouped.setdefault(namespace, []).append(pod)
        return grouped

    def _matching_pods(
        self,
        pods: list[dict[str, Any]],
        selector: dict[str, str],
    ) -> list[dict[str, Any]]:
        matches = []
        for pod in pods:
            labels = pod.get("metadata", {}).get("labels", {})
            if all(labels.get(key) == value for key, value in selector.items()):
                matches.append(pod)
        return matches

    def _warnings(self, endpoints_success: bool, pods_success: bool) -> list[str]:
        warnings = []
        if not endpoints_success:
            warnings.append("Could not inspect endpoints")
        if not pods_success:
            warnings.append("Could not inspect pods for selector matching")
        return warnings
