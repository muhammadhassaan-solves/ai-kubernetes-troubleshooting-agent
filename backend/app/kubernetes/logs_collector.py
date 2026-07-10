from typing import Any

from app.kubernetes.kubectl import KubectlExecutor

FAILURE_KEYWORDS = (
    "exception",
    "error",
    "failed",
    "failure",
    "connection refused",
    "connection reset",
    "timeout",
    "missing",
    "not found",
    "env",
    "image",
    "startup",
    "panic",
    "traceback",
)


class LogsCollector:
    def __init__(self, kubectl: KubectlExecutor) -> None:
        self.kubectl = kubectl

    def collect_for_pods(
        self,
        problematic_pods: list[dict[str, Any]],
        max_pods: int = 5,
        tail_lines: int = 120,
    ) -> dict[str, Any]:
        collected_logs = []

        for pod in problematic_pods[:max_pods]:
            namespace = pod.get("namespace", "default")
            name = pod.get("name", "")
            if not name:
                continue

            result = self.kubectl.run(
                [
                    "logs",
                    name,
                    "-n",
                    namespace,
                    "--all-containers=true",
                    f"--tail={tail_lines}",
                ],
                timeout_seconds=20,
            )

            used_previous_logs = False
            if not result.success or not result.stdout.strip():
                result = self.kubectl.run(
                    [
                        "logs",
                        name,
                        "-n",
                        namespace,
                        "--all-containers=true",
                        "--previous",
                        f"--tail={tail_lines}",
                    ],
                    timeout_seconds=20,
                )
                used_previous_logs = True

            collected_logs.append(
                {
                    "pod": name,
                    "namespace": namespace,
                    "status": pod.get("status", ""),
                    "success": result.success,
                    "source": "previous" if used_previous_logs else "current",
                    "relevant_lines": self._extract_relevant_lines(result.stdout),
                    "error": result.stderr.strip() if not result.success else "",
                }
            )

        return {
            "checked_pods": len(collected_logs),
            "logs": collected_logs,
        }

    def _extract_relevant_lines(self, stdout: str, max_lines: int = 40) -> list[str]:
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        relevant = [
            line
            for line in lines
            if any(keyword in line.lower() for keyword in FAILURE_KEYWORDS)
        ]

        if relevant:
            return relevant[-max_lines:]

        return lines[-min(max_lines, 20) :]

