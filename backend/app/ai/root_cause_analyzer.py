import json
from typing import Any

from loguru import logger

from app.ai.confidence_engine import ConfidenceEngine
from app.ai.fix_recommendation import FixRecommendationEngine
from app.ai.llm_client import LLMClientError, OpenRouterClient
from app.ai.prompt_builder import PromptBuilder


class RootCauseAnalyzer:
    def __init__(self) -> None:
        self.prompt_builder = PromptBuilder()
        self.llm_client = OpenRouterClient()
        self.fix_engine = FixRecommendationEngine()
        self.confidence_engine = ConfidenceEngine()

    async def analyze(self, investigation: dict[str, Any]) -> dict[str, Any]:
        deterministic_diagnosis = self._deterministic_diagnosis(investigation)
        if deterministic_diagnosis:
            diagnosis = self._ensure_shape(deterministic_diagnosis)
            diagnosis = self.fix_engine.normalize(diagnosis)
            return self.confidence_engine.normalize(diagnosis)

        messages = self.prompt_builder.build_messages(investigation)

        try:
            content = await self.llm_client.complete(messages)
            diagnosis = self._parse_json(content)
        except LLMClientError as error:
            logger.warning("AI diagnosis unavailable: {}", error)
            diagnosis = self._fallback_diagnosis(investigation, str(error))

        diagnosis = self._ensure_shape(diagnosis)
        diagnosis = self.fix_engine.normalize(diagnosis)
        diagnosis = self.confidence_engine.normalize(diagnosis)
        return diagnosis

    def _deterministic_diagnosis(
        self,
        investigation: dict[str, Any],
    ) -> dict[str, Any] | None:
        errors = [
            section.get("error", "")
            for section in investigation.values()
            if isinstance(section, dict) and section.get("error")
        ]

        if errors:
            combined = " ".join(errors).lower()
            if "kubectl executable was not found" in combined:
                return {
                    "root_cause": "kubectl is not installed or not available to the backend",
                    "explanation": "The backend could not run kubectl, so it cannot inspect the selected Kubernetes cluster.",
                    "fix": "Install kubectl in the backend runtime and make sure it is available on PATH.",
                    "kubectl_commands": ["kubectl version --client", "kubectl config get-contexts"],
                    "prevention": "Include kubectl in the backend image and verify it during deployment health checks.",
                    "confidence": 98,
                    "confidence_reasoning": "High confidence because every Kubernetes collection step failed before reaching the cluster.",
                }

            if "kubeconfig" in combined or "context" in combined or "cluster" in combined:
                return {
                    "root_cause": "Unable to connect to the selected Kubernetes cluster",
                    "explanation": "Kubernetes evidence collection failed while using kubectl. This usually means the kubeconfig path, selected context, permissions, or cluster network access is not valid from the backend runtime.",
                    "fix": "Verify the kubeconfig path, selected context, cluster access, and kubectl permissions for the backend process.",
                    "kubectl_commands": ["kubectl config get-contexts", "kubectl cluster-info", "kubectl auth can-i get pods -A"],
                    "prevention": "Run a startup check that validates kubeconfig, current context, and required read permissions.",
                    "confidence": 90,
                    "confidence_reasoning": "High confidence because kubectl failed before returning cluster resources.",
                }

        problematic_pods = investigation.get("pods", {}).get("problematic_pods", [])
        for pod in problematic_pods:
            if pod.get("status") == "Error" and pod.get("exit_code", 0) != 0:
                pod_name = pod.get("name", "the pod")
                namespace = pod.get("namespace", "default")
                exit_code = pod.get("exit_code")
                log_lines = self._log_lines_for_pod(investigation, pod_name, namespace)
                log_summary = " ".join(log_lines[:3]) if log_lines else "No application error log was captured."

                return {
                    "root_cause": f"{pod_name} exited with a non-zero status",
                    "explanation": f"Pod {namespace}/{pod_name} terminated with status Error and exit code {exit_code}. The captured logs show: {log_summary}",
                    "fix": "Inspect the container startup command, required environment variables, and application configuration, then update the pod or owning workload so the process exits successfully.",
                    "kubectl_commands": [
                        f"kubectl logs {pod_name} -n {namespace}",
                        f"kubectl describe pod {pod_name} -n {namespace}",
                    ],
                    "prevention": "Use readiness checks, clear startup logging, and deployment smoke tests so non-zero exits are caught before promotion.",
                    "confidence": 88,
                    "confidence_reasoning": "High confidence because Kubernetes reports the container terminated with Error and a non-zero exit code.",
                }

        healthy_sections = [
            section.get("healthy")
            for section in investigation.values()
            if isinstance(section, dict) and "healthy" in section
        ]
        no_logs = investigation.get("logs", {}).get("checked_pods") == 0

        if healthy_sections and all(healthy is True for healthy in healthy_sections) and no_logs:
            return {
                "root_cause": "No critical Kubernetes issues detected",
                "explanation": "Pods, events, deployments, and networking checks did not report unhealthy resources.",
                "fix": "No immediate Kubernetes fix is required. Continue monitoring the cluster and investigate application-level symptoms if users still report problems.",
                "kubectl_commands": ["kubectl get pods -A", "kubectl get events -A"],
                "prevention": "Keep readiness probes, resource limits, alerting, and deployment checks in place.",
                "confidence": 85,
                "confidence_reasoning": "Medium-high confidence because the investigation found no critical Kubernetes signals, though deeper app-level checks may still be needed.",
            }

        return None

    def _log_lines_for_pod(
        self,
        investigation: dict[str, Any],
        pod_name: str,
        namespace: str,
    ) -> list[str]:
        logs = investigation.get("logs", {}).get("logs", [])
        for log in logs:
            if log.get("pod") == pod_name and log.get("namespace") == namespace:
                return log.get("relevant_lines", [])
        return []

    def _parse_json(self, content: str) -> dict[str, Any]:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start < 0 or end < 0:
                raise LLMClientError("OpenRouter response was not valid JSON")
            parsed = json.loads(content[start : end + 1])

        if not isinstance(parsed, dict):
            raise LLMClientError("OpenRouter response JSON was not an object")

        return parsed

    def _ensure_shape(self, diagnosis: dict[str, Any]) -> dict[str, Any]:
        return {
            "root_cause": diagnosis.get("root_cause", "Unable to determine root cause"),
            "explanation": diagnosis.get("explanation", "The available evidence was inconclusive."),
            "fix": diagnosis.get("fix", ""),
            "kubectl_commands": diagnosis.get("kubectl_commands")
            or diagnosis.get("kubectl_command")
            or [],
            "prevention": diagnosis.get("prevention", ""),
            "confidence": diagnosis.get("confidence", 0),
            "confidence_reasoning": diagnosis.get("confidence_reasoning", ""),
        }

    def _fallback_diagnosis(
        self,
        investigation: dict[str, Any],
        error_message: str,
    ) -> dict[str, Any]:
        pod_error = investigation.get("pods", {}).get("error")
        if pod_error:
            explanation = f"Kubernetes evidence collection reported: {pod_error}"
        else:
            explanation = "AI reasoning could not run, but Kubernetes evidence was collected."

        return {
            "root_cause": "AI diagnosis unavailable",
            "explanation": explanation,
            "fix": "Verify OPENROUTER_API_KEY and OPENROUTER_MODEL are configured on the backend, then retry the investigation.",
            "kubectl_commands": ["kubectl get pods -A", "kubectl get events -A"],
            "prevention": "Keep server-side AI environment variables configured and monitor API failures.",
            "confidence": 0,
            "confidence_reasoning": error_message,
        }
