import json
from typing import Any

from app.kubernetes.kubectl import KubectlExecutor, KubectlResult

IMPORTANT_REASONS = {
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "Unhealthy",
}


class EventsAnalyzer:
    def __init__(self, kubectl: KubectlExecutor) -> None:
        self.kubectl = kubectl

    def analyze(self, max_events: int = 50) -> dict[str, Any]:
        result = self.kubectl.run(["get", "events", "-A", "-o", "json"])
        if not result.success:
            return self._failure(result)

        payload = json.loads(result.stdout or "{}")
        findings = []

        for event in payload.get("items", []):
            reason = event.get("reason", "")
            message = event.get("message", "")
            if reason not in IMPORTANT_REASONS:
                continue

            metadata = event.get("metadata", {})
            involved_object = event.get("involvedObject", {})
            findings.append(
                {
                    "namespace": metadata.get("namespace", "default"),
                    "reason": reason,
                    "message": message,
                    "object_kind": involved_object.get("kind", ""),
                    "object_name": involved_object.get("name", ""),
                    "count": event.get("count", 1),
                    "last_seen": event.get("lastTimestamp")
                    or event.get("eventTime")
                    or event.get("metadata", {}).get("creationTimestamp", ""),
                }
            )

        return {
            "healthy": len(findings) == 0,
            "findings": findings[-max_events:],
        }

    def _failure(self, result: KubectlResult) -> dict[str, Any]:
        return {
            "healthy": False,
            "findings": [],
            "error": result.stderr.strip(),
        }

