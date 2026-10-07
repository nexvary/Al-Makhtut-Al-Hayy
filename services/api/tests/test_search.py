from app.citations import CitationTarget
from app.search import InMemorySearchIndex, SearchDocument


def test_search_prefers_verified_document() -> None:
    index = InMemorySearchIndex()
    citation = CitationTarget(manuscript_id="m", page_id="p")
    index.upsert(SearchDocument(id="a", text="اداة جراحية", citation=citation, verified=False))
    index.upsert(SearchDocument(id="b", text="اداة جراحية", citation=citation, verified=True))
    hits = index.search("أداة جراحية")
    assert hits[0].document.id == "b"
