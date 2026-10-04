from app.ai_lab import EvidenceOnlyAI, LabRequest, LabTask
from app.comparison import word_differences
from app.living import LayerKind, LayerProvenance, LivingLayer, ReviewState, SourceAnchor


def reading(region="r", **kwargs):
    return LivingLayer(kind=LayerKind.DRAFT, text="Test reading, not historical content",
                       provenance=LayerProvenance(source=SourceAnchor(manuscript_id="m", page_id="p",
                       region_id=region), extraction_method="manual"), **kwargs)


def test_lab_never_borrows_neighboring_region_or_invents_translation():
    service = EvidenceOnlyAI()
    request = LabRequest(source=SourceAnchor(manuscript_id="m", page_id="p", region_id="r"),
                         question="What does this say?")
    answer = service.answer(request, [reading("other")])
    assert answer.insufficient_evidence and not answer.evidence
    answer = service.answer(request, [reading()])
    assert answer.evidence[0].state == ReviewState.DRAFT
    assert answer.evidence[0].provenance.confidence is None
    request.task = LabTask.TRANSLATE
    request.target_language = "ar"
    assert service.answer(request, [reading()]).insufficient_evidence


def test_lab_latest_revision_keeps_machine_label():
    first = reading()
    second = reading(parent_revision_id=first.id)
    machine = LivingLayer(kind=LayerKind.MACHINE, state=ReviewState.MACHINE, text="Uncertain?",
                          provenance=LayerProvenance(source=first.provenance.source,
                          extraction_method="htr", model="fixture-model"))
    request = LabRequest(source=first.provenance.source, question="Is this certain?")
    answer = EvidenceOnlyAI().answer(request, [first, second, machine])
    assert [e.revision_id for e in answer.evidence] == [second.id, machine.id]
    assert answer.evidence[1].state == ReviewState.MACHINE


def test_word_comparison_preserves_omissions_and_additions():
    diff = word_differences("alpha beta", "alpha gamma beta")
    assert any(x.operation == "insert" and x.right == ["gamma"] for x in diff)
    diff = word_differences("alpha beta", "alpha")
    assert diff[-1].operation == "delete" and diff[-1].left == ["beta"]
