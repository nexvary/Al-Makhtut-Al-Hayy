from __future__ import annotations

from pydantic import BaseModel, Field

from .grounding import AnswerClaim, Evidence, GroundedAnswer, validate_grounded_answer
from .search import HybridRetriever, SearchDocument, SqliteSearchIndex


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    limit: int = Field(default=6, ge=1, le=20)


class AskService:
    """Retrieval-first Q&A.

    No generative provider is called in the foundation implementation.
    It returns sourced excerpts; an LLM adapter can later transform them
    into claims, but only through GroundedAnswer validation.
    """

    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever

    def ask(self, request: AskRequest) -> GroundedAnswer:
        hits = self.retriever.search(request.question, limit=request.limit)
        if not hits:
            return GroundedAnswer(
                question=request.question,
                insufficient_evidence=True,
            )

        evidence = [
            Evidence(
                id=hit.document.id,
                text=hit.document.text,
                citation=hit.document.citation,
                verified=hit.document.verified,
            )
            for hit in hits
        ]
        claims = [
            AnswerClaim(
                text="تم العثور على مقاطع مرتبطة بالسؤال. راجع الأدلة المرفقة قبل اعتماد أي تفسير.",
                evidence_ids=[item.id for item in evidence],
            )
        ]
        return validate_grounded_answer(
            GroundedAnswer(question=request.question, claims=claims, evidence=evidence)
        )


search_index = SqliteSearchIndex()
qa_service = AskService(HybridRetriever(search_index))


def index_document(document: SearchDocument) -> None:
    search_index.upsert(document)
