from app.heritage_qa import HeritageQuestion, LivingEvidenceCorpus
from app.living import LayerKind, LayerProvenance, LivingLayer, ReviewState, SourceAnchor
from app.living_store import SqliteLayerRepository


def reviewed(text="Synthetic fracture treatment fixture", **kwargs):
    return LivingLayer(kind=LayerKind.VERIFIED,state=ReviewState.VERIFIED,text=text,language="en",
                       provenance=LayerProvenance(source=SourceAnchor(manuscript_id="m",page_id="p"),
                       extraction_method="manual",reviewer="reviewer"),**kwargs)


def test_corpus_keeps_verified_evidence_and_source_filters(tmp_path):
    store=SqliteLayerRepository(tmp_path / "living.sqlite3")
    first=reviewed()
    store.append(first,actor="reviewer")
    draft=LivingLayer(kind=LayerKind.DRAFT,text="Synthetic fracture unrelated draft",provenance=first.provenance)
    store.append(draft,actor="editor")
    corpus=LivingEvidenceCorpus(store)
    hits=corpus.search(HeritageQuestion(question="fracture"))
    assert [h.revision_id for h in hits]==[first.id]
    assert hits[0].provenance.confidence is None
    assert not corpus.search(HeritageQuestion(question="fracture",manuscript_ids=["other"]))
    assert not corpus.search(HeritageQuestion(question="fracture",language="ar"))
    assert not corpus.search(HeritageQuestion(question="unknown question"))
    store.append(reviewed(text="Updated synthetic fixture",parent_revision_id=first.id),actor="reviewer")
    assert not corpus.search(HeritageQuestion(question="fracture"))
