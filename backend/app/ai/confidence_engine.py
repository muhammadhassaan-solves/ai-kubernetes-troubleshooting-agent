from typing import Any


class ConfidenceEngine:
    def normalize(self, diagnosis: dict[str, Any]) -> dict[str, Any]:
        confidence = diagnosis.get("confidence", 0)

        try:
            confidence = int(confidence)
        except (TypeError, ValueError):
            confidence = 0

        diagnosis["confidence"] = max(0, min(confidence, 100))

        if not diagnosis.get("confidence_reasoning"):
            diagnosis["confidence_reasoning"] = self._default_reasoning(
                diagnosis["confidence"],
            )

        return diagnosis

    def _default_reasoning(self, confidence: int) -> str:
        if confidence >= 80:
            return "High confidence because the evidence strongly points to one failure mode."
        if confidence >= 50:
            return "Medium confidence because the evidence suggests a likely cause but is incomplete."
        return "Low confidence because the available evidence is incomplete or inconclusive."

