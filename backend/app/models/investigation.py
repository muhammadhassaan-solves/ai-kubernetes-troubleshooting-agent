from typing import Any

from pydantic import BaseModel


class InvestigationResponse(BaseModel):
    status: str
    diagnosis: dict[str, Any]
    investigation: dict[str, Any]


class InvestigationRequest(BaseModel):
    kube_context: str | None = None
    realtime_channel: str | None = None


class ClusterContextsResponse(BaseModel):
    status: str
    contexts: list[str]
    current_context: str = ""
    error: str = ""
