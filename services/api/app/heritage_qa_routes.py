from typing import Annotated

from fastapi import APIRouter, Depends

from .heritage_qa import EvidenceCorpus, HeritageAnswer, HeritageQuestion, LivingEvidenceCorpus
from .living_routes import layer_repository
from .living_store import SqliteLayerRepository
from .repository import repository
from .scholarship import scholarship_store

router = APIRouter(prefix="/api/v1/heritage", tags=["ask-the-heritage"])


def evidence_corpus(store: Annotated[SqliteLayerRepository, Depends(layer_repository)]) -> EvidenceCorpus:
    return LivingEvidenceCorpus(store)


@router.post("/ask", response_model=HeritageAnswer)
def ask_heritage(request: HeritageQuestion, corpus: Annotated[EvidenceCorpus, Depends(evidence_corpus)]):
    if request.work_id:
        witnesses = {w.manuscript_id for w in scholarship_store.witnesses(request.work_id) if w.manuscript_id}
        associated = {m.id for m in repository.list() if m.work_id == request.work_id or m.id in witnesses}
        selected = associated if request.manuscript_ids is None else associated.intersection(request.manuscript_ids)
        request = request.model_copy(update={"manuscript_ids": sorted(selected)})
    evidence = corpus.search(request)
    return HeritageAnswer(question=request.question, evidence=evidence, insufficient_evidence=not evidence)
