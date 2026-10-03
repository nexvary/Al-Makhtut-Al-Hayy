from __future__ import annotations

from pydantic import BaseModel, Field

from .citations import CitationTarget, citation_key


class Evidence(BaseModel):
    id: str
    text: str
    citation: CitationTarget
    verified: bool = False


class AnswerClaim(BaseModel):
    text: str
    evidence_ids: list[str] = Field(default_factory=list)


class GroundedAnswer(BaseModel):
    question: str
    claims: list[AnswerClaim] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    insufficient_evidence: bool = False


class UnsupportedClaimError(ValueError):
    pass


def validate_grounded_answer(answer: GroundedAnswer) -> GroundedAnswer:
    evidence_ids = {item.id for item in answer.evidence}
    for claim in answer.claims:
        if not claim.evidence_ids:
            raise UnsupportedClaimError("Every factual claim must cite evidence")
        missing = set(claim.evidence_ids) - evidence_ids
        if missing:
            raise UnsupportedClaimError(f"Unknown evidence IDs: {sorted(missing)}")
    return answer


def evidence_coverage(answer: GroundedAnswer) -> float:
    if not answer.claims:
        return 1.0 if answer.insufficient_evidence else 0.0
    supported = sum(1 for claim in answer.claims if claim.evidence_ids)
    return supported / len(answer.claims)


def evidence_labels(answer: GroundedAnswer) -> dict[str, str]:
    return {item.id: citation_key(item.citation) for item in answer.evidence}
