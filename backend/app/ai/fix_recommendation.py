from typing import Any


class FixRecommendationEngine:
    def normalize(self, diagnosis: dict[str, Any]) -> dict[str, Any]:
        commands = diagnosis.get("kubectl_commands", [])

        if isinstance(commands, str):
            commands = [commands]

        if not isinstance(commands, list):
            commands = []

        diagnosis["kubectl_commands"] = [
            str(command).strip()
            for command in commands
            if str(command).strip().startswith("kubectl ")
        ]
        diagnosis["kubectl_command"] = (
            diagnosis["kubectl_commands"][0]
            if diagnosis["kubectl_commands"]
            else ""
        )

        if not diagnosis.get("fix"):
            diagnosis["fix"] = "Review the Kubernetes evidence and apply the smallest safe configuration change."

        if not diagnosis.get("prevention"):
            diagnosis["prevention"] = "Add readiness checks, deployment validation, and monitoring for this failure mode."

        return diagnosis
