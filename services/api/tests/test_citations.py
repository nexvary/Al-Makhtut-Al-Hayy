from app.citations import CitationTarget, citation_key


def test_region_citation_key_is_stable() -> None:
    target = CitationTarget(manuscript_id="m1", page_id="p3", region_id="r7")
    assert citation_key(target) == "m1:p3:r7"
