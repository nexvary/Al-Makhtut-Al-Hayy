import pytest

from app.citations import CitationTarget
from app.editorial import EditorialStore, ReviewState, TextRevision
from app.knowledge import GlossaryStore, GlossaryTerm
from app.models import TextLayerKind
from app.search import HybridRetriever, SearchDocument, SqliteSearchIndex
from app.visual_knowledge import HistoricalObject, VisualKnowledgeStore


def test_compatibility_records_survive_restart_and_retain_history(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    glossary = GlossaryStore(path)
    glossary.put(GlossaryTerm(id="word",term="Synthetic term",definition="First fixture"),actor="reviewer")
    glossary.put(GlossaryTerm(id="word",term="Synthetic term",definition="Second fixture"),actor="reviewer")
    assert GlossaryStore(path).list()[0].definition == "Second fixture"
    assert len(glossary.store.history("glossary","word")) == 2
    visual = VisualKnowledgeStore(path)
    visual.put_object(HistoricalObject(id="object",manuscript_id="synthetic",name="Synthetic",category="surgery"),actor="reviewer")
    assert VisualKnowledgeStore(path).list_objects("synthetic")[0].warnings
    index = SqliteSearchIndex(path)
    index.upsert(SearchDocument("document","Synthetic instrument",CitationTarget(manuscript_id="synthetic",page_id="p1")))
    assert SqliteSearchIndex(path).search("instrument")[0].document.citation.page_id == "p1"


def test_semantic_only_results_resolve_real_documents_not_unknown_ids(tmp_path):
    index = SqliteSearchIndex(tmp_path / "legacy.sqlite3")
    index.upsert(SearchDocument("known","Synthetic tool",CitationTarget(manuscript_id="synthetic",page_id="p1")))
    class VectorFixture:
        def search(self, query, *, limit):
            return [("invented-id",1.0),("known",0.8)]
    hits = HybridRetriever(index,VectorFixture()).search("different term")
    assert [hit.document.id for hit in hits] == ["known"]
    assert hits[0].vector_score == 0.8


def test_legacy_htr_never_becomes_verified_and_first_parent_is_checked(tmp_path):
    store = EditorialStore(tmp_path / "legacy.sqlite3")
    revision = TextRevision(manuscript_id="synthetic",page_id="p1",region_id="r1",layer_kind=TextLayerKind.HTR_RAW,
                            text="Uncertain synthetic reading",state=ReviewState.VERIFIED,created_by="reviewer")
    with pytest.raises(ValueError,match="HTR"):
        store.add_revision(revision)
    revision.state = ReviewState.MACHINE
    revision.parent_revision_id = "missing"
    with pytest.raises(ValueError,match="parent"):
        store.add_revision(revision)
