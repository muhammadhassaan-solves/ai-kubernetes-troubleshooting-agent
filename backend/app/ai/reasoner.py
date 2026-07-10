from typing import Any

from app.ai.root_cause_analyzer import RootCauseAnalyzer


async def generate_diagnosis(investigation: dict[str, Any]) -> dict[str, Any]:
    return await RootCauseAnalyzer().analyze(investigation)
