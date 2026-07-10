from typing import Any

from app.kubernetes.deployment_inspector import DeploymentInspector
from app.kubernetes.events_analyzer import EventsAnalyzer
from app.kubernetes.kubectl import KubectlExecutor
from app.kubernetes.logs_collector import LogsCollector
from app.kubernetes.network_inspector import NetworkInspector
from app.kubernetes.pod_inspector import PodInspector


class InvestigationService:
    def __init__(self, kube_context: str | None = None) -> None:
        self.kubectl = KubectlExecutor(context=kube_context)
        self.pod_inspector = PodInspector(self.kubectl)
        self.logs_collector = LogsCollector(self.kubectl)
        self.events_analyzer = EventsAnalyzer(self.kubectl)
        self.deployment_inspector = DeploymentInspector(self.kubectl)
        self.network_inspector = NetworkInspector(self.kubectl)

    def run(self) -> dict[str, Any]:
        pods = self.pod_inspector.inspect()
        logs = self.logs_collector.collect_for_pods(
            pods.get("problematic_pods", []),
        )
        events = self.events_analyzer.analyze()
        deployments = self.deployment_inspector.inspect()
        network = self.network_inspector.inspect()

        return {
            "pods": pods,
            "logs": logs,
            "events": events,
            "deployments": deployments,
            "network": network,
        }


def investigate_cluster() -> dict[str, Any]:
    return InvestigationService().run()
