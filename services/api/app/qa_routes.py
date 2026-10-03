from fastapi import APIRouter

from .grounding import GroundedAnswer
from .qa import AskRequest, qa_service

router = APIRouter(prefix="/api/v1/qa", tags=["qa"])


@router.post("/ask", response_model=GroundedAnswer)
def ask_manuscript(request: AskRequest) -> GroundedAnswer:
    return qa_service.ask(request)
