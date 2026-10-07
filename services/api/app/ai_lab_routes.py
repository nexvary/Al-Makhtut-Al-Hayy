from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from .ai_lab import AIService, EvidenceOnlyAI, LabAnswer, LabRequest
from .living_routes import layer_repository
from .living_store import SqliteLayerRepository
from .repository import repository

router = APIRouter(prefix="/api/v1/ai-lab", tags=["manuscript-ai-lab"])


def ai_service() -> AIService:
    return EvidenceOnlyAI()


@router.post("/ask", response_model=LabAnswer)
def ask_region(request: LabRequest,
               store: Annotated[SqliteLayerRepository, Depends(layer_repository)],
               service: Annotated[AIService, Depends(ai_service)]) -> LabAnswer:
    manuscript = repository.get(request.source.manuscript_id)
    page = next((p for p in manuscript.pages if p.id == request.source.page_id), None) if manuscript else None
    if page is None:
        raise HTTPException(404, "Source page not found")
    if request.source.region_id and not any(r.id == request.source.region_id for r in page.regions):
        raise HTTPException(404, "Source region not found")
    return service.answer(request, store.history(manuscript.id, page.id))
