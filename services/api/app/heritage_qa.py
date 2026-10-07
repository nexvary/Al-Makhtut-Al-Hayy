"""Evidence corpus abstraction: reviewed retrieval, no unsourced generated answer."""
from typing import Protocol

from pydantic import BaseModel, Field

from .ai_lab import LabEvidence
from .arabic import tokenize_arabic
from .living import LayerKind
from .living_store import SqliteLayerRepository


class HeritageQuestion(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    manuscript_ids: list[str] | None = Field(default=None, max_length=100)
    work_id: str | None = Field(default=None, max_length=100)
    language: str | None = Field(default=None, max_length=35)
    limit: int = Field(default=6, ge=1, le=20)


class CorpusEvidence(LabEvidence):
    retrieval_score: float


class HeritageAnswer(BaseModel):
    question: str
    evidence: list[CorpusEvidence] = Field(default_factory=list)
    insufficient_evidence: bool
    provider: str = "reviewed-source-excerpts"
    message: str = "Search excerpts are evidence, not an invented historical synthesis."
    candidate_limit: int = 2000


class EvidenceCorpus(Protocol):
    def search(self, request: HeritageQuestion) -> list[CorpusEvidence]: ...


class LivingEvidenceCorpus:
    def __init__(self, store: SqliteLayerRepository):
        self.store = store

    def search(self, request: HeritageQuestion) -> list[CorpusEvidence]:
        terms = set(tokenize_arabic(request.question))
        if not terms:
            return []
        hits = []
        kinds = {LayerKind.VERIFIED, LayerKind.CRITICAL, LayerKind.MODERN, LayerKind.TRANSLATION}
        for layer in self.store.verified_candidates(request.manuscript_ids):
            if not layer.text or layer.kind not in kinds or (request.language and layer.language != request.language):
                continue
            overlap = terms.intersection(tokenize_arabic(layer.text))
            if not overlap:
                continue
            hits.append(CorpusEvidence(revision_id=layer.id, text=layer.text, kind=layer.kind,
                                      state=layer.state, provenance=layer.provenance,
                                      retrieval_score=len(overlap) / len(terms)))
        return sorted(hits, key=lambda h: h.retrieval_score, reverse=True)[:request.limit]
