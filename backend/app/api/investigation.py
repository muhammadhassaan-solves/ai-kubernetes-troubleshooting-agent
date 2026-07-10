from fastapi import APIRouter, Body

from app.ai.reasoner import generate_diagnosis
from app.kubernetes.kubectl import KubectlExecutor
from app.models.investigation import (
    ClusterContextsResponse,
    InvestigationRequest,
    InvestigationResponse,
)
from app.services.investigation_service import InvestigationService

router = APIRouter(tags=["investigation"])


@router.get("/clusters", response_model=ClusterContextsResponse)
async def list_clusters() -> ClusterContextsResponse:
    result = KubectlExecutor().list_contexts()
    return ClusterContextsResponse(
        status="success" if result["healthy"] else "error",
        contexts=result["contexts"],
        current_context=result["current_context"],
        error=result["error"],
    )


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate_cluster(
    request: InvestigationRequest = Body(default_factory=InvestigationRequest),
) -> InvestigationResponse:
    investigation = InvestigationService(kube_context=request.kube_context).run()
    diagnosis = await generate_diagnosis(investigation)
    return InvestigationResponse(
        status="success",
        diagnosis=diagnosis,
        investigation=investigation,
    )
