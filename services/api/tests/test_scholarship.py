from app.citations import CitationTarget
from app.models import Manuscript, Page, Point, Region, TextLayer, TextLayerKind
from app.scholarly_export import (
    iiif_supplementing_annotation_page,
    research_bundle,
    scholarly_citation,
    tei_xml,
)


def manuscript() -> Manuscript:
    return Manuscript(
        id="m",
        title="كتاب",
        pages=[
            Page(
                id="p",
                sequence=1,
                image="image.jpg",
                canvas_uri="https://example.test/canvas/p",
                regions=[
                    Region(
                        id="r",
                        polygon=[
                            Point(x=1, y=2),
                            Point(x=11, y=2),
                            Point(x=11, y=8),
                            Point(x=1, y=8),
                        ],
                        layers=[
                            TextLayer(
                                kind=TextLayerKind.VERIFIED,
                                text="نص موثق",
                                status="verified",
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_tei_and_iiif_exports() -> None:
    item = manuscript()
    assert "نص موثق" in tei_xml(item)
    annotations = iiif_supplementing_annotation_page(item, "p")
    assert annotations["items"][0]["motivation"] == "supplementing"
    assert "#xywh=1,2,10,6" in annotations["items"][0]["target"]


def test_research_bundle_and_citation() -> None:
    witness = Witness(
        id="w",
        work_id="work",
        manuscript_id="m",
        kind=WitnessKind.MANUSCRIPT,
        label="نسخة",
        bibliography=BibliographicMetadata(title="كتاب"),
    )
    assert "witnesses" in research_bundle(manuscript(), [witness])
    target = CitationTarget(manuscript_id="m", page_id="p", region_id="r")
    assert scholarly_citation(target, base_uri="https://x.test").endswith("/p#region=r")
