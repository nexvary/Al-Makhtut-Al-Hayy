"""Provider-neutral lab. Offline implementation returns evidence, never invented readings."""
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field

from .living import LayerKind, LayerProvenance, LivingLayer, ReviewState, SourceAnchor


class LabTask(StrEnum):
    READ = "read"
    CONFIDENCE = "confidence"
    ALTERNATIVES = "alternatives"
    EXPLAIN = "explain"
    TRANSLATE = "translate"


class LabRequest(BaseModel):
    source: SourceAnchor
    question: str = Field(min_length=2, max_length=2000)
    task: LabTask = LabTask.READ
    target_language: str | None = Field(default=None, max_length=35)


class LabEvidence(BaseModel):
    revision_id: str
    text: str
    kind: LayerKind
    state: ReviewState
    provenance: LayerProvenance


class LabAnswer(BaseModel):
    question: str
    task: LabTask
    evidence: list[LabEvidence] = Field(default_factory=list)
    insufficient_evidence: bool = True
    provider: str = "source-excerpts"
    message: str = "No documented reading is available; the source remains uncertain."


class AIService(Protocol):
    def answer(self, request: LabRequest, layers: list[LivingLayer]) -> LabAnswer: ...


class EvidenceOnlyAI:
    def answer(self, request: LabRequest, layers: list[LivingLayer]) -> LabAnswer:
        selected = []
        for layer in layers:
            anchor = layer.provenance.source
            if (anchor.manuscript_id != request.source.manuscript_id
                    or anchor.page_id != request.source.page_id
                    or anchor.region_id != request.source.region_id
                    or (request.source.witness_id and anchor.witness_id != request.source.witness_id)):
                continue
            selected.append(layer)
        kinds = {
            LabTask.READ: {LayerKind.MACHINE, LayerKind.DRAFT, LayerKind.VERIFIED, LayerKind.CRITICAL},
            LabTask.CONFIDENCE: {LayerKind.MACHINE, LayerKind.DRAFT, LayerKind.VERIFIED, LayerKind.CRITICAL},
            LabTask.ALTERNATIVES: {LayerKind.MACHINE, LayerKind.DRAFT, LayerKind.VERIFIED, LayerKind.CRITICAL},
            LabTask.EXPLAIN: {LayerKind.EXPLANATION},
            LabTask.TRANSLATE: {LayerKind.TRANSLATION},
        }[request.task]
        # Keep current revision for each representation; earlier versions remain in history.
        latest = {}
        for layer in selected:
            if layer.kind in kinds and layer.text:
                if request.task == LabTask.TRANSLATE and layer.language != request.target_language:
                    continue
                latest[(layer.kind, layer.language, layer.provenance.source.witness_id)] = layer
        evidence = [LabEvidence(revision_id=x.id, text=x.text, kind=x.kind,
                                state=x.state, provenance=x.provenance) for x in latest.values()]
        return LabAnswer(question=request.question, task=request.task, evidence=evidence,
                         insufficient_evidence=not evidence,
                         message=("Documented excerpts only; machine and draft readings remain unverified."
                                  if evidence else "No documented output for this task; no text was invented."))
