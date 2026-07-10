import json
from typing import Any


class PromptBuilder:
    def build_messages(self, investigation: dict[str, Any]) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": self._system_prompt(),
            },
            {
                "role": "user",
                "content": self._user_prompt(investigation),
            },
        ]

    def _system_prompt(self) -> str:
        return """
You are a Senior Kubernetes SRE helping troubleshoot a live incident.

Your job:
1. Correlate pod status, logs, events, deployment health, and networking findings.
2. Identify the most likely root cause.
3. Explain the reasoning using specific evidence.
4. Recommend practical Kubernetes fixes.
5. Provide kubectl commands a beginner can run safely.
6. Provide a confidence score from 0 to 100.

Rules:
- Do not invent resources, namespaces, logs, or events.
- If evidence is missing, say what is missing.
- Prefer the simplest root cause that explains the evidence.
- Be specific and Kubernetes-focused.
- Return only valid JSON.
""".strip()

    def _user_prompt(self, investigation: dict[str, Any]) -> str:
        evidence = json.dumps(investigation, indent=2, sort_keys=True)
        return f"""
Analyze this Kubernetes investigation evidence.

Evidence sections:
- Pod Status
- Logs
- Events
- Deployment Health
- Networking Findings

Return this exact JSON shape:
{{
  "root_cause": "short specific root cause",
  "explanation": "clear explanation that correlates the evidence",
  "fix": "beginner-friendly Kubernetes-specific fix",
  "kubectl_commands": ["kubectl command 1", "kubectl command 2"],
  "prevention": "how to prevent this issue next time",
  "confidence": 0,
  "confidence_reasoning": "why this confidence score is appropriate"
}}

Kubernetes investigation evidence:
{evidence}
""".strip()

