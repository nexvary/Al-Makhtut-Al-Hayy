import pytest

from app.citations import CitationTarget
from app.grounding import (
    AnswerClaim,
    Evidence,
    GroundedAnswer,
    UnsupportedClaimError,
    validate_grounded_answer,
)


def test_rejects_claim_without_evidence() -> None:
    answer = GroundedAnswer(question="س", claims=[AnswerClaim(text="ادعاء")])
    with pytest.raises(UnsupportedClaimError):
        validate_grounded_answer(answer)


def test_accepts_known_evidence() -> None:
    evidence = Evidence(
        id="e1",
        text="نص",
        citation=CitationTarget(manuscript_id="m", page_id="p", region_id="r"),
    )
    answer = GroundedAnswer(
        question="س",
        claims=[AnswerClaim(text="قول", evidence_ids=["e1"])],
        evidence=[evidence],
    )
    assert validate_grounded_answer(answer) == answer
